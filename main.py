from __future__ import annotations
from typing import Dict, List, Tuple
from langchain_community.document_loaders import PyPDFLoader
import requests
import os
import pandas as pd
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

from src.utilities import _download_pdf, _build_or_load_vector_store_from_pdf, _build_or_load_vector_store_from_excel, _read_queryprompt, _retrieve_with_threshold, _read_mermaid_file, _read_excel_file, LldGpmIDs, GpmClasses
from src.langchain import build_rag_chain
from config import *
import datetime

def get_current_datetime_components():
    """Returns the current year, month, day, hour, and minute as formatted strings."""
    now = datetime.datetime.now()
    return f"{now.strftime("%Y")}-{now.strftime("%m")}-{now.strftime("%d")}-{now.strftime("%H")}-{now.strftime("%M")}"
    

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
    # vectordb, _ = _build_or_load_vector_store_from_pdf(PDF_PATH, PERSIST_DIR)
    vectordb, _ = _build_or_load_vector_store_from_excel("./documents/domain_knowledge.xlsx", PERSIST_DIR, update=False, RAG_MODE=False)
    vectordb, _ = _build_or_load_vector_store_from_excel("./documents/gpm_tips.xlsx", PERSIST_DIR, update=False, RAG_MODE=False)

    # Build chain
    rag_chain = build_rag_chain(vectordb, RAG_MODE=False)

    # Example usage
    history: List[Tuple[str, str]] = []  # placeholder for chat history if you have it
    target = _read_excel_file(TARGET_PATH)

    result = rag_chain.invoke({"question": target, "chat_history": history})
    print(f"Result keys: {result.keys()}")
    print(f"Result answer keys: {result['answer'].keys()}")

    # Pretty print
    print("=== Answer of LLD ===")
    lld_gpm_ids: LldGpmIDs = result["answer"]["lld_gpm_ids_knowledge"]
    gpm_classes: GpmClasses = result["answer"]["gpm_classes"]
    target_with_gpm = pd.read_excel(TARGET_PATH)
    target_with_gpm["ClassID"] = pd.Series(lld_gpm_ids.IDs)
    print(f"GPM Classes: {type(gpm_classes)}")
    # print(f"GPM Classes Keys: {gpm_classes.keys()}")
    target_with_gpm["ClassName"] = pd.Series(gpm_classes.ClassNames)
    target_with_gpm["Knowledge"] = pd.Series(lld_gpm_ids.knowledge)
    target_with_gpm.to_excel(f"./outputs/nikkeiBP_LLDs_with_GPM-{get_current_datetime_components()}.xlsx", index=False, engine='openpyxl')

    print("=== Answer of GPM ===")
    gpm_file = pd.DataFrame(gpm_classes.IDs, columns=["ClassID"])
    gpm_file["ClassName"] = pd.Series(gpm_classes.ClassNames)
    gpm_file["PartOf"] = pd.Series(gpm_classes.PartOfs)
    gpm_file["RelationKnowledge"] = pd.Series(gpm_classes.RelationKnowledge)
    gpm_file.to_excel(f"./outputs/nikkeiBP_GPM_classes-{get_current_datetime_components()}.xlsx", index=False, engine='openpyxl')

    print("\n=== Sources ===")
    if result["sources"]:
        for i, (src, page) in enumerate(result["sources"], start=1):
            page_str = f"p.{page}" if page != -1 else "p.?";
            print(f"{i}. {src} ({page_str})")
    else:
        print("No sufficiently relevant sources found or RAG Mode is off.")

if __name__ == "__main__":
    main()