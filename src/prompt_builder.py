from typing import List, Dict
from config import SYSTEM_PROMPT, KEYWORD_LIST, TIPS_OF_ACTION_CLASSIFICATION, DOMAIN_KNOWLEDGE, NUMBER_OF_GROUPS, NUMBER_OF_TOP, NUMBER_FOR_EACH_CONTAINER, EVALUATION_CRITERIA
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

def build_prompt(examples: Dict[str, str]) -> str:
    """
    Args:
        examples: A dictionary of examples with keys as the question and values as the answer.
    Returns:
        A string containing the system prompt, guideline rules, few shot examples, and the question.
    """
    full_prompt = f"""
    {SYSTEM_PROMPT}\n
    {TIPS_OF_ACTION_CLASSIFICATION}\n
    {DOMAIN_KNOWLEDGE}\n
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
- [ ] You should make sure that the **operation names** of GPM classes express the **operations** of LLD actions, which they are based on.
- [ ] You should make sure that the **target objects** of GPM classes' names express the **target objects** of LLD actions' names, which they are based on.

### Step 3: Map each action to Groups

- [ ] Each action should be assigned the ID and name of its group from Step2.
  - [ ] The action names should express **operations** of engineering process in Japanese.
- [ ] Source and Knowldge of action classification should be listed not only from **keyword list**, **tips of action classification** and **domain knowledge** but also from your knowledge.

### Step 4: Evaluate the classification of LLD actions and the knowledge of action classification.

- [ ] Based on the provided information and knowledge, evaluate the classification of LLD actions and the knowledge of action classification.
  - [ ] If you find actions which are not assigned any group name, you should assign a group name to them.
  - [ ] You must not make blanks on **ClassName**.
- [ ] Then, refine and improve the categorization of LLD actions into GPM classes, referring to the **Sources** section.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
   - It should start from 1 and be consecutive.
  - ClassName
    - The name should be **operations** of engineering process in Japanese.
  - Knowledge

## Constraints

- [ ] The number of groups should be about **{NUMBER_OF_GROUPS}**.
- [ ] If there are actions that are not assigned to any group, you need to create a new group for them.
- [ ] You must not make blanks on **ClassName**.
- [ ] There should be no actions left unassigned.
- [ ] You should assign the ID and name of the group to **every** action.

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
- [ ] Based on the group of LLD actions, you need to identify the **input** and **output** of the classes.
- [ ] You should refer to the **tips of action classification** and **domain knowledge** to group the classes.

### Step 2: Find the Partof relationship

- [ ] Find the **Partof** relationship between the classes based on the **input** and **output** of the classes.
  - [ ] if the verb of a class is a part of the verb of another class, then the first class is a part of the second class.
- [ ] You should express how you found the **Partof** relationship as **RelationKnowledge**.
  - [ ] You should refer to the **Sources** section and **input** and **output** of the classes to find the **Partof** relationship.

### Step 3: Evaluate the classification of GPM classes and the knowledge of action relationship.

- [ ] Based on the provided information and knowledge, evaluate the classification of GPM classes and the knowledge of action relationship.
  - [ ] If you find classes which are not assigned any group name, you should assign a group name to them.
- [ ] Then, refine and improve the categorization of GPM classes, referring to the **Sources** section.

## Format

- [ ] List all the GPM classes in a table with the following columns.

  - ClassID
    - It should start from 1 and be consecutive.
  - ClassInput
    - The input of the class.
  - ClassName
    - The name should be **operations** in Japanese.
  - ClassOutput
    - The output of the class.
  - PartOfs
    - The ID of the parent class.
  - RelationKnowledge
    - The knowledge related to the class.

## Constraints

- [ ] If there are classes that are not assigned to any group, you need to create a new group for them.
- [ ] There should be no classes left unassigned.
- [ ] if the action is not a part of any class, the **PartOfs** should be **0**.
            \n\n"""
            "Context:\n{lld_gpm_ids_knowledge}\n\nAnswer:"
        ),
    ]
)

prompt_lld_grouping = ChatPromptTemplate.from_messages(
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

Based on the provided information and knowledge, group into GPM classes by gradually detailing the classification of LLD actions based on the given **Sources** section and **Work Process** section.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Work Process

### Step 1: List all the actions

- [ ] Explicitly list each action from the logs

### Step 2: Classify actions by the most general classification

- [ ] Categorize them based on their similarities into groups of GPM classes based on the **keyword list**.
- [ ] You should refer to the **tips of action classification** and **domain knowledge** to classify the actions.
- [ ] The number of this most general classification should be **{NUMBER_OF_TOP}**.
- [ ] You should clarify the reason of the classification.

### Step 3: Classify actions by more specific classification

- [ ] Some groups should be further classified into subgroups **recursively**.
  - [ ] This process should be repeated until the total number of gpm classes is about **{NUMBER_OF_GROUPS}**.
  - [ ] Some LLD actions are not assigned to more specific classification, while others are assigned to more specific classification.
- [ ] Source and Knowldge of action classification should be listed not only from **keyword list**, **tips of action classification** and **domain knowledge** but also from your knowledge.
- [ ] You should clarify the reason of the classification.

### Step 4: Assign the GPM ID and Class Name to every action

- [ ] Assign the GPM ID to every action.
  - [ ] The ID should start from 1 and be consecutive.
- [ ] Based on the process of Step 2 and Step 3, construct the PartOf relationships between GPM actions.
  - [ ] You should clarify the reason of 


### Step 5: Evaluate the classification of LLD actions and the knowledge of action classification

- [ ] Based on the provided information and knowledge, evaluate the classification of LLD actions and the knowledge of action classification.
  - [ ] If you find actions which are not assigned any GPM ID, you should assign a GPM ID to them.
- [ ] Based on the provided information and knowledge, evaluate the PartOf relationships between GPM actions.
- [ ] Then, refine and improve the categorization of LLD actions into GPM classes and the PartOf relationships between GPM actions, referring to the **Sources** section.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
    - Integer. It is the ID of the GPM class that the LLD action belongs to.
    - The number of class IDs should be the **same** as the number of **LLD actions**.
  - PartOf
    - Integer. It should be the ID of the parent GPM class that the GPM class is part of.
    - If the action is the top level action, it should be 0.
  - ClassificationReason
    - String. It should be the reason of the classification of LLD actions to GPM classes.
  - PartOfReason
    - String. It should be the reason of the PartOf relationship of GPM classes.

## Constraints

- [ ] The total number of GPM classes should be about **{NUMBER_OF_GROUPS}**.
- [ ] The number of class IDs should be exactly **the same as the number of LLD actions**.
- [ ] If there are actions that are not assigned to any group, you need to create a new group for them.
- [ ] You must not make blanks on **ClassID** and **PartOf**.
- [ ] There should be no actions left unassigned.
- [ ] You should assign the ID and name of the group to **every** action.

            \n\n"""
            "LLD Data:\n{lld_data}\n\nAnswer:\n"
        ),
    ]
)

prompt_gpm_reconstruction = ChatPromptTemplate.from_messages(
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

Based on the categorization of LLD actions into GPM classes, reconstruct the GPM classes and their input, output, and intention, referring to the given **Sources** section and **Work Process** section.

## Sources

- The output should be based on the given keyword list, tips of action classification, and the domain knowledge.

Keyword List: \n{KEYWORD_LIST}

Tips of Action Classification: \n{TIPS_OF_ACTION_CLASSIFICATION}

Domain Knowledge: \n{DOMAIN_KNOWLEDGE}

## Work Process

### Step 1: Analyze LLD action classification and PartOf relationships of GPM classes

- [ ] Analyze the LLD action classification and PartOf relationships of GPM classes.
- [ ] Check the correspondence between the LLD actions and their GPM classes.

### Step 2: Reconstruct the elements of GPM classes

- [ ] Reconstruct the elements of GPM classes based on the **Sources** section.
  - [ ] You should reconstruct the input, output, and intention of every GPM class based on those of the LLD actions which each GPM class is made of.
- [ ] You should clarify the reason of the reconstruction.

### Step 3: Evaluate the reconstruction of GPM classes and the reasoning process

- [ ] Based on the provided information and knowledge, evaluate the reconstruction of GPM classes.
- [ ] Then, refine and improve the reconstruction of GPM classes, referring to the **Sources** section.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
    - Integer given by GPM Grouping Data. It should start from 1 and be consecutive.
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

## Constraints

- [ ] You must not make blanks on **ClassName**.
- [ ] The total number of GPM classes should be exactly the same as the number of ClassIDs in the **GPM Grouping Data**.
- [ ] There should be no GPM classes left unassigned.
- [ ] You should assign the ID and name of the group to **every** GPM class.

            \n\n"""
            "LLD Data:\n{lld_data}\n\nGPM Grouping Data:\n{gpm_grouping_data}\n\nAnswer:\n"
        ),
    ]
)

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
