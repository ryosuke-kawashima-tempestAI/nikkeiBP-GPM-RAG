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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from src.utilities import _download_pdf, _build_or_load_vector_store, _read_queryprompt, _retrieve_with_threshold, _unique_sources, _format_context_for_prompt
=======
=======
>>>>>>> Stashed changes
from src.utilities import _download_pdf, _build_or_load_vector_store_from_pdf, _build_or_load_vector_store_from_excel, _read_queryprompt, _retrieve_with_threshold, _unique_sources, LldGpmIDs, GpmClasses
# -----------------------------
# SYSTEM SETUP
# -----------------------------

SYSTEM_PROMPT = """
# Engineering Process Actions Categorization and Grouping

## Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a sandwitch factory, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the sandwich factory.

## Guidelines

- LLD is an abbreaviation for Low Level Descriptions, which are detailed logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

"""

# -----------------------------
# PROMPT TEMPLATE
# -----------------------------
prompt_lld_file = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            """
## Task

Based on the provided information and knowledge, analyze and categorize actions from improvement process logs of the sandwich factory.
- [ ] First, extract all actions from the logs.
- [ ] Then categorize them based on their similarities.
- [ ] Finally, group similar actions together to form a structured representation of the improvement process with the **source** and **knowledge** you referred to.\n\n"""
            "Context:\n{chat_history}\n\nLLD Actions: {question}\n\nAnswer:"
        ),
    ]
)
prompt_gpm_file = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            """
## Task

Based on the categorization of LLD actions and gained GPM classes, analyze the PartOf relationships among the GPM Classes.
- [ ] First, analyze the correspondence of the LLD actions to the GPM classes based on the IDs.
- [ ] Then, create a list of GPM classes with their IDs, ClassNames, and parent of the PartOf relations.\n\n"""
            "Context:\n{lld_gpm_ids_knowledge}\n\nAnswer:"
        ),
    ]
)
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

# -----------------------------
# RAG Chain (LangChain)
# -----------------------------

def build_rag_chain(vectordb: Chroma):
    """Build a RAG pipeline that returns both the answer and its sources.

    This graph avoids `.select(...)` and composes two branches in parallel:
    one to compute the LLM answer, the other to carry the sources.

    Args:
        vectordb: Prepared Chroma vector store.

    Returns:
        A runnable that, when invoked with:
            {"question": str, "chat_history": list}
        returns:
            {"answer": str, "sources": List[Tuple[str, int]]}
    """
    llm = ChatOpenAI(
        model="gpt-5",
        temperature=0,
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

<<<<<<< Updated upstream
<<<<<<< Updated upstream
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a Knowledge Engineer, responsible for designing models that capture and structure process knowledge, making it both understandable and reusable."
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template(
                "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
            ),
        ]
    )
=======
    lld_gmp_llm = llm.with_structured_output(LldGpmIDs)
    gpm_classes_llm = llm.with_structured_output(GpmClasses)
>>>>>>> Stashed changes
=======
    lld_gmp_llm = llm.with_structured_output(LldGpmIDs)
    gpm_classes_llm = llm.with_structured_output(GpmClasses)
>>>>>>> Stashed changes

    # Make the dictionary to store the output and resources!!!
    def _prepare(input_dict: Dict, top_k = 10, relevance_threshold=0.01) -> Dict:
        """Prepare retrieval results and derived fields for prompting.

        Args:
            input_dict: Dict with keys "question" and optional "chat_history".

        Returns:
            Dict containing question, chat_history, docs, context, sources.
        """
        question = input_dict["question"]
        chat_history = input_dict.get("chat_history", [])
        docs = _retrieve_with_threshold(vectordb, question, top_k, relevance_threshold)
        context = _format_context_for_prompt(docs)
        sources = _unique_sources(docs)
        lld_gpm_ids_knowledge = []
        gpm_claasses = []

        # Stores the IDs of LLD and GPM
        return {
            "question": question,
            "chat_history": chat_history,
            "docs": docs,
            "context": context,
            "sources": sources,
            "lld_gpm_ids_knowledge": lld_gpm_ids_knowledge,
            "gpm_classes": gpm_claasses,
        }

    prepare_node = RunnableLambda(_prepare)

    # Branch that generates the model answer (keeps only what the prompt expects)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    answer_branch = (
        RunnableLambda(lambda x: {"question": x["question"], "chat_history": x["chat_history"], "context": x["context"]})
        | prompt
        | llm
        | StrOutputParser()
=======
=======
>>>>>>> Stashed changes
    lld_file_branch = (
        RunnableLambda(lambda x: {"question": x["question"], "chat_history": x["chat_history"]})
        | prompt_lld_file
        | lld_gmp_llm
        | RunnableLambda(lambda x: {"lld_gpm_ids_knowledge": x["lld_gpm_ids_knowledge"].to_string()})
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    )

    gpm_file_branch = (
        prompt_gpm_file
        | gpm_classes_llm
        | RunnableLambda(lambda x: {"gpm_classes": x["gpm_classes"].to_string()})
    )

    answer_branch = lld_file_branch | gpm_file_branch

    # Branch that passes sources through untouched
    sources_branch = RunnableLambda(lambda x: x["sources"])

    # Run both branches in parallel and return combined dictionary
    pipeline = prepare_node | RunnableParallel(answer=answer_branch, sources=sources_branch)

    return pipeline
