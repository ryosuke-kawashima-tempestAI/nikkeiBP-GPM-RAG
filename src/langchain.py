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
from src.prompt_builder import prompt_lld_file, prompt_gpm_file

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

# -----------------------------
# Reserve for future use
# -----------------------------
def create_robust_lld_gpm_chain(llm_lld_grouping: ChatOpenAI, llm_gpm_reconstruction: ChatOpenAI) -> RunnableLambda:
    """
    1. Group LLD actions into GPM classes.
    2. Give Names, Input, Output, and PartOf relationships to GPM classes.
    """
    def _prepare(input_dict: Dict) -> Dict:
        return {
            "lld_data": input_dict["lld_data"],
            "number_of_lld_actions": input_dict["number_of_lld_actions"]
        }
    
    def robust_grouping(input_dict: Dict) -> Dict:
        lld_data_str = input_dict["lld_data"]
        number_of_lld_actions = input_dict["number_of_lld_actions"]
        feedback = ""
        
        # Base chain (Prompt -> LLM -> Dict)
        base_chain = robust_prompt_lld_grouping | llm_lld_grouping | RunnableLambda(lambda x: x.to_dict())
        
        max_retries = 5
        for attempt in range(max_retries):
            print(f"Executing LLD Grouping... Attempt {attempt + 1}/{max_retries}")
            try:
                # Invoke the chain. We must pass 'feedback' because we added it to the prompt.
                # If first attempt, feedback is empty string.
                result = base_chain.invoke({
                    "lld_data": lld_data_str,
                    "number_of_lld_actions": number_of_lld_actions,
                    "feedback": feedback
                })
                
                # Validation
                generated_ids = result.get("ClassIDs", [])
                
                # Ensure other list fields are present and same length (basic check)
                # The model should generate parallel lists.
                
                count_generated = len(generated_ids)
                
                if count_generated == number_of_lld_actions:
                    print("Validation successful: Output count matches input count.")
                    return result
                else:
                    print(f"Validation FAILED: Expected {number_of_lld_actions} items, got {count_generated}.")
                    # feedback for next loop
                    feedback = (
                        f"\n\n**CRITICAL ERROR IN PREVIOUS ATTEMPT**: "
                        f"You generated {count_generated} ClassIDs, but the dataset has EXACTLY {number_of_lld_actions} actions. "
                        f"You MUST generate exactly {number_of_lld_actions} ClassIDs (one for each action). "
                        f"Please recount and ensure 1-to-1 mapping."
                    )
                    # Save the last result in case we need to fallback
                    last_result = result
            except Exception as e:
                print(f"Error during attempt {attempt + 1}: {e}")
                feedback = f"\n\n**SYSTEM ERROR IN PREVIOUS ATTEMPT**: {str(e)}. Please output valid JSON matching the schema."
        
        # Fallback Strategy
        print(f"WARNING: Max retries exhausted. Forcing alignment of output length to {number_of_lld_actions}.")
        
        # We use the result from the last successful generation (even if length mismatch)
        # If last_result is not defined (e.g. all exceptions), we might crash, but unlikely with typical LLM behavior.
        if 'last_result' not in locals():
            raise ValueError("All attempts failed with exceptions.")
            
        final_result = last_result
        
        # List of fields to truncate/pad
        fields = ["ClassIDs", "PartOfs", "ClassificationReasons", "PartOfReasons"]
        
        for field in fields:
            data_list = final_result.get(field, [])
            current_len = len(data_list)
            
            if current_len > number_of_lld_actions:
                # Truncate
                final_result[field] = data_list[:number_of_lld_actions]
            elif current_len < number_of_lld_actions:
                # Pad
                diff = number_of_lld_actions - current_len
                # Pad with 0 for IDs, empty string for texts
                if field in ["ClassIDs", "PartOfs"]:
                    # Use 0 or the last value? 0 is safer for "No Class" or "Same as previous"
                    # But 0 for ClassID might be confusing if it means "New Group". 
                    # Let's pad with 0.
                    padding = [0] * diff
                else:
                    padding = ["(Filled by System due to Length Mismatch)"] * diff
                final_result[field] = data_list + padding
                
        return final_result

    prepare_node = RunnableLambda(_prepare)
    print("LLD Data was sucessfully deployed!")
    
    def robust_gpm_reconstruction(input_dict: Dict) -> Dict:
        lld_data_in = input_dict["lld_data"]
        gpm_grouping_data_in = input_dict["gpm_grouping_data"]
        feedback = ""
        
        base_chain = robust_prompt_gpm_reconstruction | llm_gpm_reconstruction | RunnableLambda(lambda x: x.to_dict())
        
        max_retries = 3
        
        for attempt in range(max_retries):
            print(f"Executing GPM Reconstruction... Attempt {attempt + 1}/{max_retries}")
            try:
                result = base_chain.invoke({
                    "lld_data": lld_data_in,
                    "gpm_grouping_data": gpm_grouping_data_in,
                    "feedback": feedback
                })
                
                # Check for parallel array consistency
                # Fields: ClassIDs, ClassInputs, ClassNames, ClassOutputs, ClassIntents
                fields = ["ClassIDs", "ClassInputs", "ClassNames", "ClassOutputs", "ClassIntents"]
                lengths = {f: len(result.get(f, [])) for f in fields}
                
                unique_lengths = set(lengths.values())
                if len(unique_lengths) <= 1:
                    print("Validation successful: All fields have equal length.")
                    return result
                
                print(f"Validation FAILED: Fields have inconsistent lengths: {lengths}")
                feedback = (
                    f"\n\n**CRITICAL ERROR IN PREVIOUS ATTEMPT**: "
                    f"Your output lists must all have the same length. Currently they are: {lengths}. "
                    f"Please ensure every ClassID has a corresponding Input, Name, Output, and Intent."
                )
                last_result = result
                
            except Exception as e:
                print(f"Error during GPM Reconstruction attempt {attempt + 1}: {e}")
                feedback = f"\n\n**SYSTEM ERROR IN PREVIOUS ATTEMPT**: {str(e)}."

        # Fallback
        print("WARNING: Max retries exhausted for GPM Reconstruction. Forcing alignment to minimum length.")
        if 'last_result' not in locals():
            raise ValueError("All attempts failed.")
            
        final_result = last_result
        fields = ["ClassIDs", "ClassInputs", "ClassNames", "ClassOutputs", "ClassIntents"]
        min_len = min(len(final_result.get(f, [])) for f in fields)
        
        for f in fields:
            final_result[f] = final_result.get(f, [])[:min_len]
            
        return final_result

    lld_gpm_chain = prepare_node | RunnableParallel(
        lld_input = RunnableLambda(lambda x: x),
        lld_grouping = RunnableLambda(robust_grouping),
    ) | RunnableParallel(
        lld_input = RunnableLambda(lambda x: x["lld_input"]["lld_data"]),
        lld_grouping = RunnableLambda(lambda x: x["lld_grouping"]),
        gpm_reconstruction = RunnableLambda(lambda x: {
            "lld_data": x["lld_input"]["lld_data"],
            "gpm_grouping_data": x["lld_grouping"]
        }) | RunnableLambda(robust_gpm_reconstruction),
    )
    
    return lld_gpm_chain
