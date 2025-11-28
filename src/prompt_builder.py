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
