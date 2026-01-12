from __future__ import annotations
from typing import Dict, List, Tuple
import requests
import os
import json
import pandas as pd
import glob
from operator import itemgetter
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
)
from src.utilities import _read_excel_file, get_current_datetime_components, read_excel_to_json
from config import *
import datetime
from pydantic import BaseModel

# -----------------------------
# PROMPT TEMPLATE
# -----------------------------
from src.prompt_builder import prompt_lld_grouping, prompt_gpm_reconstruction

# -----------------------------
# Output Format
# -----------------------------
class LLDandGPMOutput(BaseModel):
    LLDelements: List[LLDelement]
    GPMelements: List[GPMelement]
    def to_dict(self):
        return {
            "LLDelements": [x.to_dict() for x in self.LLDelements],
            "GPMelements": [x.to_dict() for x in self.GPMelements],
        }
    def to_json(self):
        return json.dumps(self.to_dict())

class LLDelement(BaseModel):
    ClassID: int
    ClassificationReason: str
    def to_dict(self):
        return {
            "ClassID": self.ClassID,
            "ClassificationReason": self.ClassificationReason,
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())

class GPMelement(BaseModel):
    ClassID: int
    ClassInput: str
    ClassName: str
    ClassOutput: str
    ClassIntent: str
    ClassConstructionReason: str
    PartOf: int
    PartOfReason: str
    
    def to_dict(self):
        return {
            "ClassID": self.ClassID,
            "ClassInput": self.ClassInput,
            "ClassName": self.ClassName,
            "ClassOutput": self.ClassOutput,
            "ClassIntent": self.ClassIntent,
            "ClassConstructionReason": self.ClassConstructionReason,
            "PartOf": self.PartOf,
            "PartOfReason": self.PartOfReason,
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())

# -----------------------------
# Prompt Template
# -----------------------------

prompt_lld_grouping_gpm_construction = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            SYSTEM_PROMPT,
        ),
        (
            "human",
            f"""
## Task

Based on the provided information and knowledge, 
1. group LLD actions into GPM classes by gradually detailing the classification 
2. construct the PartOf relationships between GPM actions
3. reconstruct the GPM classes and their input, output, and intention
, referring to the given **Sources** section and **Work Process** section.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Work Process

### Step 1: List all the actions

- [ ] Explicitly list each action from the logs

### Step 2: Classify actions by the most general classification

- [ ] Categorize them based on their similarities into groups of GPM classes based on the operations and objects of LLD actions.
- [ ] You should refer to the **Sources** section to classify the actions.
- [ ] The number of this most general classification should be **{NUMBER_OF_TOP}**.
- [ ] You should clarify the reason of the classification.

### Step 3: Classify actions by more specific classification

- [ ] Some groups should be further classified into subgroups **recursively**.
  - [ ] This process should be repeated as long as the total number of gpm classes is within **{NUMBER_OF_GROUPS}**.
  - [ ] Some LLD actions are not assigned to more specific classification, while others are assigned to more specific classification.
- [ ] Source and Knowldge of action classification should be listed not only from **Sources** section but also from your knowledge.
- [ ] You should clarify the reason of the classification.

### Step 4: Assign the information of GPM action to every action

- [ ] Assign the GPM ID and other elements of GPM to every action.
  - [ ] The ID should start from 1 and be consecutive.
- [ ] Based on the process of Step 2 and Step 3, construct the PartOf relationships between GPM actions.
  - [ ] You should clarify the reason of part of relationships between GPM actions.


### Step 5: Evaluate the classification of LLD actions and the knowledge of action classification

- [ ] Based on the provided information and knowledge, evaluate the classification of LLD actions and the knowledge of action classification.
  - [ ] If you find actions which are not assigned any GPM ID, you should assign a GPM ID to them.
- [ ] Based on the provided information and knowledge, evaluate the PartOf relationships between GPM actions.
- [ ] Based on the provided information and knowledge, evaluate the construction of GPM classes.
- [ ] Then, refine and improve the categorization of LLD actions into GPM classes, the PartOf relationships between GPM actions, and the construction of GPM classes, referring to the **Sources** section.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
    - Integer. It is the ID of the GPM class that the LLD action belongs to.
    - The number of class IDs should be the **same** as the number of **LLD actions**.
  - ClassificationReason
    - String. It should be the reason of the classification of LLD actions to GPM classes.
    - You should clarify which part on **Sources** section you refer to when you construct the classification of LLD actions to GPM classes.
    - You can add your own knowledge when you construct the classification of LLD actions to GPM classes.
  - PartOf
    - Integer. It should be the ID of the parent GPM class that the GPM class is part of.
    - If the action is the top level action, it should be 0.
  - PartOfReason
    - String. It should be the reason of the PartOf relationship of GPM classes.
    - You should clarify which part on **Sources** section you refer to when you construct the PartOf relationship of GPM classes.
    - You can add your own knowledge when you construct the PartOf relationship of GPM classes.
  - ClassInput
    - String. It should be the input of the action.
  - ClassName
    - String. The name should be **operations** of engineering process in Japanese.
  - ClassOutput
    - String. It should be the output of the action.
  - ClassIntention
    - String. It should be the intention of the action.
  - ReconstructionReason
    - String. It should be the reason of the reconstruction of the GPM classes.
    - You should clarify which part on **Sources** section you refer to when you construct the reconstruction of the GPM classes.
    - You can add your own knowledge when you construct the reconstruction of the GPM classes.

## Constraints

- [ ] The total number of GPM classes should be **less than {NUMBER_OF_GROUPS}**.
- [ ] The total number of GPM classes at the top should be **almost equal to {NUMBER_OF_TOP}**.
- [ ] You should **not shuffle** the order of the GPM classes.
- [ ] The number of class IDs should be exactly **the same as the number of LLD actions**.
- [ ] You must not make blanks on **ClassID**, **PartOf**, and **ClassName**.
- [ ] You should assign the ID and name of the group to **every** LLD action and GPM class.
            \n\n"""
            "LLD Data:\n{lld_data}\n\nAnswer:\n"
        ),
    ]
)

# -----------------------------
# Prompt Chain
# -----------------------------

def create_lld_gpm_chain(llm: ChatOpenAI) -> RunnableLambda:
    """
    1. Group LLD actions into GPM classes.
    2. Give Names, Input, Output, and PartOf relationships to GPM classes.
    """
    def _prepare(input_dict: Dict) -> Dict:
        return {
            "lld_data": input_dict["lld_data"],
        }
    
    prepare_node = RunnableLambda(_prepare)
    print("LLD Data was sucessfully deployed!")
    
    lld_gpm_chain = prepare_node | prompt_lld_grouping_gpm_construction | llm | RunnableLambda(lambda x: x.to_dict())
    
    return lld_gpm_chain

def main():
    """
    runs the simplest LLM workflow imaginable.
    """
    lld_data = read_excel_to_json(TARGET_PATH)
    number_of_lld_actions = len(lld_data)
    print(f"LLD Data was sucessfully loaded. Total actions: {number_of_lld_actions}")
    # LLM Setting
    llm = ChatOpenAI(
        model="gpt-5.2",
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    llm_with_format = llm.with_structured_output(LLDandGPMOutput)
    # Create LLD-GPM Chain
    lld_gpm_chain = create_lld_gpm_chain(llm_with_format)
    # Run LLD-GPM Chain
    result = lld_gpm_chain.invoke({"lld_data": lld_data})
    print("LLD-GPM Chain was sucessfully run!")
    with open(f"./outputs/result-{get_current_datetime_components()}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    df_lld_data = pd.read_excel(TARGET_PATH)
    print(f"Result Keys: {result.keys()}")
    df_lld_data["ClassID"] = pd.Series([x["ClassID"] for x in result["LLDelements"]])
    df_lld_data["ClassificationReason"] = pd.Series([x["ClassificationReason"] for x in result["LLDelements"]])
    df_gpm_data = pd.DataFrame(result["GPMelements"], columns=["ClassID", "ClassInput", "ClassName", "ClassOutput", "ClassIntent", "ClassConstructionReason", "PartOf", "PartOfReason"])

    lld_output_path = f"./outputs/LF-lldgrouping-{get_current_datetime_components()}.xlsx"
    gpm_output_path = f"./outputs/LF-gpmreconstruction-{get_current_datetime_components()}.xlsx"
    df_lld_data.to_excel(lld_output_path, index=False)
    df_gpm_data.to_excel(gpm_output_path, index=False)
    print("LLD Data was sucessfuly saved!")
    

if __name__ == "__main__":
    main()
