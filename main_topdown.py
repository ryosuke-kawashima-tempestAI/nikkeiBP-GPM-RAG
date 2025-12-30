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
class LLDGrouping(BaseModel):
    LLDGroupingElements: List[LLDGroupingElement]
    GPMPartOfElements: List[GPMPartOfElement]
    
    def to_dict(self):
        return {
            "ClassIDs": [x.ClassID for x in self.LLDGroupingElements],
            "PartOfs": [x.PartOf for x in self.GPMPartOfElements],
            "ClassificationReasons": [x.ClassificationReason for x in self.LLDGroupingElements],
            "PartOfReasons": [x.PartOfReason for x in self.GPMPartOfElements],
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())

class LLDGroupingElement(BaseModel):
    ClassID: int
    PartOf: int
    ClassificationReason: str

class GPMPartOfElement(BaseModel):
    ClassID: int
    PartOf: int
    PartOfReason: str

class GPMReconstructionElement(BaseModel):
    ClassID: int
    ClassInput: str
    ClassName: str
    ClassOutput: str
    ClassIntent: str

class GPMReconstruction(BaseModel):
    GPMReconstructionElements: List[GPMReconstructionElement]
    
    def to_dict(self):
        return {
            "ClassIDs": [x.ClassID for x in self.GPMReconstructionElements],
            "ClassInputs": [x.ClassInput for x in self.GPMReconstructionElements],
            "ClassNames": [x.ClassName for x in self.GPMReconstructionElements],
            "ClassOutputs": [x.ClassOutput for x in self.GPMReconstructionElements],
            "ClassIntents": [x.ClassIntent for x in self.GPMReconstructionElements],
        }
    
    def to_json(self):
        return json.dumps(self.to_dict())

def create_lld_gpm_chain(llm_lld_grouping: ChatOpenAI, llm_gpm_reconstruction: ChatOpenAI) -> RunnableLambda:
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
    
    lld_gpm_chain = prepare_node | RunnableParallel(
        lld_input = RunnableLambda(lambda x: x),
        lld_grouping = prompt_lld_grouping | llm_lld_grouping | RunnableLambda(lambda x: x.to_dict()),
    ) | RunnableParallel(
        lld_input = RunnableLambda(lambda x: x["lld_input"]["lld_data"]),
        lld_grouping = RunnableLambda(lambda x: x["lld_grouping"]),
        gpm_reconstruction = RunnableLambda(lambda x: {
            "lld_data": x["lld_input"]["lld_data"],
            "gpm_grouping_data": x["lld_grouping"]
        }) | prompt_gpm_reconstruction | llm_gpm_reconstruction | RunnableLambda(lambda x: x.to_dict()),
    )
    
    return lld_gpm_chain

def main():
    """
    1. Group LLD actions into GPM classes.
    2. Give Names, Input, Output, and PartOf relationships to GPM classes.
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
    llm_lld_grouping = llm.with_structured_output(LLDGrouping)
    llm_gpm_reconstruction = llm.with_structured_output(GPMReconstruction)
    print("Two LLMs were sucessfuly deployed!")
    
    lld_gpm_chain = create_lld_gpm_chain(llm_lld_grouping, llm_gpm_reconstruction)
    print("LLD GPM Chain was sucessfuly deployed!")
    
    result = lld_gpm_chain.invoke({
        "lld_data": lld_data,
    })
    print("LLD GPM Chain was sucessfuly executed!")
    with open(f"./outputs/result-{get_current_datetime_components()}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    df_lld_data = pd.read_excel(TARGET_PATH)
    df_lld_data["ClassID"] = result["lld_grouping"]["ClassIDs"]
    df_lld_data["ClassificationReason"] = result["lld_grouping"]["ClassificationReasons"]
    df_gpm_data = pd.DataFrame(result["gpm_reconstruction"])
    df_gpm_data["PartOf"] = result["lld_grouping"]["PartOfs"]
    df_gpm_data["PartOfReason"] = result["lld_grouping"]["PartOfReasons"]
    lld_output_path = f"./outputs/ma-welding-lldgrouping-{get_current_datetime_components()}.xlsx"
    gpm_output_path = f"./outputs/ma-welding-gpmreconstruction-{get_current_datetime_components()}.xlsx"
    df_lld_data.to_excel(lld_output_path, index=False)
    df_gpm_data.to_excel(gpm_output_path, index=False)
    print("LLD Data was sucessfuly saved!")

if __name__ == "__main__":
    main()
