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
from src.utilities import _download_pdf, _build_or_load_vector_store, _read_queryprompt, _retrieve_with_threshold, _unique_sources, _format_context_for_prompt

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
        return {
            "question": question,
            "chat_history": chat_history,
            "docs": docs,
            "context": context,
            "sources": sources,
        }

    prepare_node = RunnableLambda(_prepare)

    # Branch that generates the model answer (keeps only what the prompt expects)
    answer_branch = (
        RunnableLambda(lambda x: {"question": x["question"], "chat_history": x["chat_history"], "context": x["context"]})
        | prompt
        | llm
        | StrOutputParser()
    )
    # Branch that passes sources through untouched
    sources_branch = RunnableLambda(lambda x: x["sources"])

    # Run both branches in parallel and return combined dictionary
    pipeline = prepare_node | RunnableParallel(answer=answer_branch, sources=sources_branch)

    return pipeline