from typing import List, Dict
from config import SYSTEM_PROMPT, GUIDELINE_RULES, FEW_SHOT_EXAMPLES

def build_prompt(examples: Dict[str, str]) -> str:
    """
    Args:
        examples: A dictionary of examples with keys as the question and values as the answer.
    Returns:
        A string containing the system prompt, guideline rules, few shot examples, and the question.
    """
    full_prompt = f"""
    {SYSTEM_PROMPT}
    {GUIDELINE_RULES}
    {examples}
    """
    return full_prompt
    
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
