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
from src.utilities import _download_pdf, _build_or_load_vector_store_from_pdf, _build_or_load_vector_store_from_excel, _format_context_for_prompt, _retrieve_with_threshold, _unique_sources, LldGpmIDs, GpmClasses
from config import *

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
            f"""
## Task

Based on the provided information and knowledge, analyze and categorize LLD actions from improvement process logs based on the given **Sources** section and **Work Process** section.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Work Process

### Step 1: List all the actions

- [ ] Explicitly list each action from the logs

### Step 2: Classify actions

- [ ] Categorize them based on their similarities into groups of GPM classes based on the **keyword list**.
- [ ] You should refer to the **tips of action classification** and **domain knowledge** to classify the actions.

### Step 3: Map each action to Groups

- [ ] Each action should be assigned the ID and name of its group from Step2.
- [ ] Source and Knowldge of action classification should be listed not only from **keyword list**, **tips of action classification** and **domain knowledge** but also from your knowledge.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
  - ClassName
    - The name should be in Japanese.
  - Knowledge

## Constraints

- [ ] The number of groups should be about **{NUMBER_OF_GROUPS}**.
- [ ] If there are actions that are not assigned to any group, you need to create a new group for them.
- [ ] There should be no actions left unassigned.

            \n\n"""
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
        (
            "human",
            f"""
## Task

Based on the provided given information about LLD action classification, create a GPM class relations. You should find the **Partof** relationship between the classes.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Work Process

### Step 1: Group the GPM classes

- [ ] Gather classes which deal with the same object, which can be from **keyword list**.
- [ ] You should refer to the **tips of action classification** and **domain knowledge** to group the classes.

### Step 2: Find the Partof relationship

- [ ] Find the **Partof** relationship between the classes.
  - [ ] if the verb of a class is a part of the verb of another class, then the first class is a part of the second class.
- [ ] You should express how you found the **Partof** relationship as **RelationKnowledge**.

## Format

- [ ] List all the GPM classes in a table with the following columns.

  - ClassID
  - ClassName
    - The name should be in Japanese.
  - PartOfs
    - The ID of the parent class.
  - RelationKnowledge
    - The knowledge related to the class.

## Constraints

- [ ] If there are classes that are not assigned to any group, you need to create a new group for them.
- [ ] There should be no classes left unassigned.
            \n\n"""
            "Context:\n{lld_gpm_ids_knowledge}\n\nAnswer:"
        ),
    ]
)

# -----------------------------
# RAG Chain (LangChain)
# -----------------------------

def build_rag_chain(vectordb: Chroma, RAG_MODE: bool = True):
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
    print("LLM has been initialized")

    lld_gpm_llm = llm.with_structured_output(LldGpmIDs)
    gpm_classes_llm = llm.with_structured_output(GpmClasses)

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
        docs = _retrieve_with_threshold(vectordb, question, top_k, relevance_threshold) if RAG_MODE else []
        context = _format_context_for_prompt(docs)
        sources = _unique_sources(docs)

        # Stores the IDs of LLD and GPM
        return {
            "question": question,
            "chat_history": chat_history,
            "docs": docs,
            "context": context,
            "sources": sources,
        }

    prepare_node = RunnableLambda(_prepare)
    print("Prepare node has been initialized")

    # Branch that generates the model answer (keeps only what the prompt expects)
    # x is the data dictionary coming from the previous node
    lld_file_branch = (
        RunnableLambda(lambda x: {"question": x["question"], "chat_history": x["chat_history"]})
        | prompt_lld_file
        | lld_gpm_llm
        | RunnableLambda(lambda x: {"lld_gpm_ids_knowledge": x})
    )

    # The output: {
    # "original": {"question": "...","chat_history": [...],"sources": [...],"context": "...",...},
    # "lld": {"lld_gpm_ids_knowledge": <LLMResult>}}
    combined_branch = RunnableParallel(
        original = lambda x: x,
        lld = lld_file_branch,
    )

    gpm_file_branch = (
        RunnableLambda(lambda x: {"lld_gpm_ids_knowledge": x["lld"]["lld_gpm_ids_knowledge"]})
        | prompt_gpm_file
        | gpm_classes_llm
        | RunnableLambda(lambda x: {"gpm_classes": x})
    )

    # Combine_branch already inherits "original" and "lld" from [original]
    answer_branch = RunnableParallel(
        original = combined_branch | itemgetter("original"),
        lld_gpm_ids_knowledge = combined_branch | itemgetter("lld") | itemgetter("lld_gpm_ids_knowledge"),
        gpm_classes = combined_branch | gpm_file_branch | itemgetter("gpm_classes"),
    )

    # Branch that passes sources through untouched
    sources_branch = RunnableLambda(lambda x: x["sources"])

    # Run both branches in parallel and return combined dictionary
    pipeline = prepare_node | RunnableParallel(answer=answer_branch, sources=sources_branch)

    return pipeline
