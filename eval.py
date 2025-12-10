from __future__ import annotations
from typing import Dict, List, Tuple
import requests
import os
import json
import pandas as pd
import glob
from operator import itemgetter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from src.utilities import _read_excel_file, get_current_datetime_components
from config import *
import datetime
LLD_GPM_DATA_PATH = "./eval_target/LF_merged_lld_gpm-2025-12-08-17-28.xlsx"
from pydantic import BaseModel

# -----------------------------
# PROMPT TEMPLATE
# -----------------------------
prompt_evaluation = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        # MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            f"""
## Task

Based on the provided information and knowledge, analyze and evaluate the following two based on the given **Sources** section, **Evaluation Criteria** section, and **Work Process** section.

1. The classification of LLD actions into GPM classes.
2. The PartOf relationships between GPM classes.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Evaluation Criteria

You need to evaluate the classification of LLD actions into GPM classes and the PartOf relationships between GPM classes.
Then, you need to state why the classification and PartOf relationships are good or bad and how to improve them based on the criteria.

Evaluation Criteria: \n{EVALUATION_CRITERIA}

## Work Process

### Step 1: Analyze LLD actions

- [ ] Analyze the LLD actions, referring to the Log numbers. If the log numbers are the same, it means the actions are executed in the same engineering process.
- [ ] You need to focus on the **input**, **Action**, and **Output** of each action.
- [ ] You may consider the Intention, Annotation, Rationale, and Tools/Knowledge of each action.

### Step 2: Evaluate the correspondence between LLD actions and GPM classes

- Each LLD action is assigned to a GPM class with **ClassID** and **ClassName_y**.
- The reason of the classification is listed in **Knowledge**.
- [ ] You need to judge whether the LLD actions with the same GPM class should be merged.
- [ ] You need to judge whether the LLD actions with the different GPM classes should be split.
- [ ] You need to state why the classification is good or bad and how to improve it based on the criteria.
    - [ ] refer to the **Sources** section and **Evaluation Criteria** section.
- [ ] You need to suggest how to improve the classification of LLD actions into GPM classes.
    - [ ] refer to the **Sources** section and **Evaluation Criteria** section.

### Step 3: Analyze GPM Classes

- [ ] Analyze the GPM classes, referring to the **ClassInput**, **ClassName_x**, **ClassName_y**, and **ClassOutput**.

### Step 4: Evaluate the PartOf relationships between GPM classes

- The GPM action being PartOf 0 means that it is located at the top of engineering process.
- The reason of the PartOf relationship is listed in **RelationKnowledge**.
- [ ] You need to judge whether the GPM actions within the same GPM class should be merged.
    - [ ] You should refer to the corresponding LLD actions and their sequencial relationship.
- [ ] You need to judge whether the GPM actions separated into the different GPM classes should be split.
    - [ ] You should refer to the corresponding LLD actions and their sequencial relationship.
- [ ] You need to state why the PartOf relationships are good or bad and how to improve it based on the criteria.
    - [ ] refer to the **Sources** section and **Evaluation Criteria** section.

## Format

- [ ] List the evaluation results in a table with the following columns.
- [ ] Show the reasons of the evaluation results.

### LLD to GPM Evaluation

- LLDtoGPM
    - the corresponding LLD actions and GPM classes you evaluated.
- LLDtoGPMEvaluation
    - the evaluation results of the classification of LLD actions into GPM classes.
- LLDtoGPMEvaluationReason
    - the reasons of the evaluation results of the classification of LLD actions into GPM classes.
- LLDtoGPMEvaluationImprovement
    - the improvement suggestions for the classification of LLD actions into GPM classes.
- LLDtoGPMEvaluationImprovementReason
    - the reasons of the improvement suggestions for the classification of LLD actions into GPM classes.

### GPM PartOf Evaluation

- PartOfGPM
    - the GPM classes you evaluated the PartOf relationships between.
- PartOfEvaluation
    - the evaluation results of the PartOf relationships between GPM classes.
- PartOfEvaluationReason
    - the reasons of the evaluation results of the PartOf relationships between GPM classes.
- PartOfImprovement
    - the improvement suggestions for the PartOf relationships between GPM classes.
- PartOfEvaluationImprovementReason
    - the reasons of the improvement suggestions for the PartOf relationships between GPM classes.

## Constraints

- [ ] The output should be in Japanese.
- [ ] You may cite references of your outputs.
- [ ] You should refer to the **Sources** section and **Evaluation Criteria** section.

            \n\n"""
            "LLD Actions and GPM Classes: {question}\n\nAnswer:"
        ),
    ]
)

# -----------------------------
# Output Format
# -----------------------------

class OutputEvaluation(BaseModel):
    """
    Output format for the evaluation of the GPM output
    """
    # LLD to GPM Evaluation
    LLDtoGPM: List[str]
    LLDtoGPMEvaluation: List[str]
    LLDtoGPMEvaluationReason: List[str]
    LLDtoGPMEvaluationImprovement: List[str]
    LLDtoGPMEvaluationImprovementReason: List[str]
    # GPM PartOf Evaluation
    PartOfGPM: List[str]
    PartOfEvaluation: List[str]
    PartOfEvaluationReason: List[str]
    PartOfImprovement: List[str]
    PartOfEvaluationImprovementReason: List[str]
    

# -----------------------------
# Main
# -----------------------------

def main():
    """
    Main function to evaluate the GPM Output
    """
    ## Data Loading
    lld_gpm_data = _read_excel_file(LLD_GPM_DATA_PATH)
    print("LLD and GPM are read.")
    # LLM Settings
    llm = ChatOpenAI(
        model="gpt-5",
        temperature=0,
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    llm_with_output_format = llm.with_structured_output(OutputEvaluation)
    print("LLM has been initialized")

    ## Prompt
    evaluation_chain = prompt_evaluation | llm_with_output_format
    evaluation_result = evaluation_chain.invoke({"question": lld_gpm_data})

    ## Save the result
    ### Save as JSON
    # Convert Pydantic object to dict and create DataFrame
    res_dict = evaluation_result.dict()
    timestamp = get_current_datetime_components()
    
    # Save as JSON text
    json_path = f"./outputs/learningFactory_GPM_eval-{timestamp}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(res_dict, f, indent=4, ensure_ascii=False)
    print(f"Evaluation results saved to:\n- {json_path}")
    
    ### Save as Excel
    """
    df_evaluation = pd.DataFrame({
        "LLDtoGPM": evaluation_result.LLDtoGPM,
        "LLDtoGPMEvaluation": evaluation_result.LLDtoGPMEvaluation,
        "LLDtoGPMEvaluationReason": evaluation_result.LLDtoGPMEvaluationReason,
        "LLDtoGPMEvaluationImprovement": evaluation_result.LLDtoGPMEvaluationImprovement,
        "LLDtoGPMEvaluationImprovementReason": evaluation_result.LLDtoGPMEvaluationImprovementReason,
        "PartOfGPM": evaluation_result.PartOfGPM,
        "PartOfEvaluation": evaluation_result.PartOfEvaluation,
        "PartOfEvaluationReason": evaluation_result.PartOfEvaluationReason,
        "PartOfImprovement": evaluation_result.PartOfImprovement,
        "PartOfEvaluationImprovementReason": evaluation_result.PartOfEvaluationImprovementReason
    })
    print("Evaluation Result has been created.")
    df_evaluation.to_excel(f"./outputs/learningFactory_GPM_eval-{get_current_datetime_components()}.xlsx", index=False, engine='openpyxl')
    """
    # Use from_dict with orient='index' -> transpose to handle lists of different lengths (pads with NaN)
    df_evaluation = pd.DataFrame.from_dict(res_dict, orient='index').transpose()
    # Reuse the timestamp to keep filenames consistent with the JSON file
    excel_path = f"./outputs/learningFactory_GPM_eval-{timestamp}.xlsx"
    df_evaluation.to_excel(excel_path, index=False, engine='openpyxl')
    
    print(f"Evaluation results saved to:\n- {excel_path}")
    
if __name__ == "__main__":
    main()
