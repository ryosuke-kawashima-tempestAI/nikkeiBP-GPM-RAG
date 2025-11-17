from __future__ import annotations
from typing import Dict, List, Tuple
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
import requests
import os
import glob
import pandas as pd
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
# -----------------------------
# Configuration
# -----------------------------

APIKEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = APIKEY

# -----------------------------
# Utilities Functions
# -----------------------------

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

def _build_or_load_vector_store_from_pdf(pdf_path: str, persist_dir: str, update=False) -> Tuple[Chroma, List[Document]]:
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

def _build_or_load_vector_store_from_excel(excel_path: str, persist_dir: str, update=False) -> Tuple[Chroma, List[Document]]:
    """Load Excel file, chunk its content, and build/persist a Chroma vector store.

    This function is idempotent—if a persisted DB exists, it will be reused.

    Args:
        excel_path: Path to the source Excel (.xlsx) file.
        persist_dir: Chroma persistence directory.
    Returns:
        A tuple of (vector_store, all_chunks).
    """
    loader = UnstructuredExcelLoader(excel_path)
    docs = loader.load()
    print(f"Document's Pages: {len(docs)}")
    page_median = len(docs) // 2
    print(f"{page_median}th page: {docs[page_median].page_content[:100]}")
    
    # Chunk by row to preserve data integrity
    chunks = []
    for doc in docs:
        # Each row becomes a separate chunk
        # metadata can record the sheet name and row number if needed
        chunks.append(Document(
            page_content=doc.page_content,
            metadata=doc.metadata
        ))

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
        if update:
            print("Updating existing Chroma DB with new chunks.")
            vectordb.add_documents(chunks)
    else:
        print(f"Creating new Chroma DB in {persist_dir}")
        vectordb = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=persist_dir,
        )

    return vectordb, chunks

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

def _read_excel_file(file_path: str) -> str:
    """Read an Excel (.xlsx) file and return its contents as a pandas DataFrame.

    This function safely reads the content of an Excel file, handling common
    issues such as file not found or read errors.

    Args:
        file_path: Path to the Excel (.xlsx) file to read.
    Returns:
        A pandas DataFrame containing the Excel data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    if path.suffix.lower() != ".xlsx":
        print(f"⚠️ Warning: '{file_path}' does not have a .xlsx extension.")
    df = pd.read_excel(file_path)
    docs = []
    for i, row in df.iterrows():
        text = "\n".join(f"{k}: {v}" for k, v in row.to_dict().items())
        docs.append(
            Document(
                page_content=text,
                metadata={"row_index": int(i), "source": os.path.basename(file_path)},
            )
        )
    combined_text = "\n\n".join(doc.page_content for doc in docs)
    return combined_text