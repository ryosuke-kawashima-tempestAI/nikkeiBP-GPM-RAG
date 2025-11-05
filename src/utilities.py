from __future__ import annotations
from typing import Dict, List, Tuple
from langchain_community.document_loaders import PyPDFLoader
import requests
import os
import glob
from operator import itemgetter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    # SystemMessage, # Removed incorrect import
)
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_core.documents import Document
from pathlib import Path

def _download_pdf(url: str, dst_path: str) -> None:
    """Download a PDF if it does not exist.

    Args:
        url: HTTP(S) URL to the PDF file.
        dst_path: Local file path to save the content.
    """
    if os.path.exists(dst_path):
        return
    headers = {"User-Agent": "Mozilla/5.0 (LangChain RAG Example)"}
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    with open(dst_path, "wb") as f:
        f.write(resp.content)

def _build_or_load_vector_store(pdf_path: str, persist_dir: str) -> Tuple[Chroma, List[Document]]:
    """Load pages, chunk them, and build/persist a Chroma vector store.

    This function is idempotent—if a persisted DB exists, it will be reused.

    Args:
        pdf_path: Path to the source PDF.
        persist_dir: Chroma persistence directory.

    Returns:
        A tuple of (vector_store, all_chunks).
    """
    # Load pages with metadata (PyPDFLoader populates "source" and "page")
    pages = PyPDFLoader(pdf_path).load()
    print(f"Document's Pages: {len(pages)}")
    page_median = len(pages) // 2
    print(f"{page_median}th page: {pages[page_median].page_content[:100]}")

    # Chunk for better retrieval granularity
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=200,
        add_start_index=True,
        separators=["\n\n", "\n", "。", "、", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    # Embeddings (OpenAI)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.environ.get("OPENAI_API_KEY")
    )

    # If DB already exists, open it; otherwise create and persist
    if os.path.isdir(persist_dir) and len(os.listdir(persist_dir)) > 0:
        print(f"Loading persisted Chroma DB from {persist_dir}")
        vectordb = Chroma(
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )
    else:
        print(f"Creating new Chroma DB in {persist_dir}")
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_dir,
        )

    return vectordb, chunks

def _format_context_for_prompt(docs: List[Document]) -> str:
    """Create a compact, source-aware context string.

    Each chunk is annotated with its source and page to aid the model and humans.

    Args:
        docs: Retrieved document chunks.

    Returns:
        A single string containing concatenated chunks with source/page headers.
    """
    formatted = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown_source")
        page = d.metadata.get("page", "unknown_page")
        formatted.append(
            f"[Chunk {i} | Source: {os.path.basename(src)} | p.{page}]\n{d.page_content.strip()}"
        )
    return "\n\n".join(formatted)

def _unique_sources(docs: List[Document]) -> List[Tuple[str, int]]:
    """Extract unique (source, page) pairs preserving order.

    Args:
        docs: Retrieved document chunks.

    Returns:
        A list of (basename, page) pairs with duplicates removed.
    """
    seen = set()
    uniq: List[Tuple[str, int]] = []
    for d in docs:
        src = os.path.basename(d.metadata.get("source", "unknown_source"))
        page = int(d.metadata.get("page", -1)) if isinstance(d.metadata.get("page"), int) else -1
        key = (src, page)
        if key not in seen:
            seen.add(key)
            uniq.append(key)
    return uniq

def _retrieve_with_threshold(vectordb: Chroma, query: str, top_k: int, threshold: float) -> List[Document]:
    """Retrieve documents with relevance score filtering to reduce hallucinations.

    Uses Chroma's `similarity_search_with_relevance_scores` and filters out
    chunks whose relevance score is below a threshold.

    Args:
        vectordb: The Chroma vector store.
        query: Natural language query.
        top_k: Number of results to request from the store.
        threshold: Minimum acceptable relevance score in [0, 1].

    Returns:
        Filtered list of Documents sorted by score descending.
    """
    scored = vectordb.similarity_search_with_relevance_scores(query, k=top_k)
    # Keep only items meeting the threshold; each item is (Document, score)
    filtered = [(doc, sc) for doc, sc in scored if sc is not None and sc >= threshold]
    # Sort by score (desc) to prioritize strongest evidence
    filtered.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in filtered]

def _read_queryprompt(path="./*.md") -> str:
    """Get the query from the local Mark Down File
    Args:
        path: the path to the Mark Down File
    Returns:
        The query string
    """
    markdown_files = glob.glob(path)
    question = ""

    for path in markdown_files:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            question += f"\n\n---\n\n{content}"

    print("Combined markdown length:", len(question))
    print(question[:len(question)//5])
    return question

def _read_mermaid_file(file_path: str) -> str:
    """Read a Mermaid (.mmd) file and return its contents as a string.

    This function safely reads the content of a Mermaid file, automatically
    handling common encodings and trimming extra whitespace.

    Args:
        file_path: Path to the Mermaid (.mmd) file to read.

    Returns:
        A string containing the full Mermaid graph definition.

    Raises:
        FileNotFoundError: If the file does not exist.
        UnicodeDecodeError: If the file encoding cannot be decoded.
        ValueError: If the file is empty.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    if path.suffix.lower() != ".mmd":
        print(f"⚠️ Warning: '{file_path}' does not have a .mmd extension.")

    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"The file '{file_path}' is empty.")

    return text