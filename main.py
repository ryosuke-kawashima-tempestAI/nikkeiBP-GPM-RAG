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
from src.utilities import _download_pdf, _build_or_load_vector_store, _read_queryprompt, _retrieve_with_threshold, _unique_sources, _format_context_for_prompt, _read_mermaid_file
from src.langchain import build_rag_chain

# -----------------------------
# Configuration
# -----------------------------
APIKEY = input("Enter your OpenAI API Key: ")
os.environ["OPENAI_API_KEY"] = APIKEY
PDF_URL = "https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r05/pdf/00zentai.pdf"
PDF_PATH = "./documents/nikkeiBP_day5.pdf"
PROMPT_PATH = "./prompts/nikkeiBP_mermaid.md"
GRAPH_PATH = "./knowledge_graphs/NikkeiBP_meronymy_hyponymy.mmd"

# Persist vector DB to avoid recomputation across runs
PERSIST_DIR = "chroma_db"

# Retrieval defaults
TOP_K = 10
RELEVANCE_THRESHOLD = 0.1  # larger (e.g., 0.3–0.5) = stricter filtering

# -----------------------------
# Main
# -----------------------------

def main() -> None:
    """Run a single RAG query and print both the answer and its sources.

    The sample question is about the trends of Generative AI. Adjust as needed.
    """
    # Validate API key
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Please export your key in the environment."
        )

    # Prepare data + vector store
    # _download_pdf(PDF_URL, PDF_PATH)
    vectordb, _ = _build_or_load_vector_store(PDF_PATH, PERSIST_DIR)

    # Build chain
    rag_chain = build_rag_chain(vectordb)

    # Example usage
    history: List[Tuple[str, str]] = []  # placeholder for chat history if you have it
    question = _read_queryprompt(PROMPT_PATH)
    graph = _read_mermaid_file(GRAPH_PATH)
    question_and_graph = f"{question}\n\nKnowledge Graph:\n{graph}"

    result = rag_chain.invoke({"question": question_and_graph, "chat_history": history})

    # Pretty print
    print("\n=== Answer ===")
    print(result["answer"].strip())

    print("\n=== Sources ===")
    if result["sources"]:
        for i, (src, page) in enumerate(result["sources"], start=1):
            page_str = f"p.{page}" if page != -1 else "p.?";
            print(f"{i}. {src} ({page_str})")
    else:
        print("No sufficiently relevant sources found (the model should answer with 'I don't know').")

if __name__ == "__main__":
    main()