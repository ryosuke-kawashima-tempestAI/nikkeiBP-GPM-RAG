from typing import List, Dict
from config import SYSTEM_PROMPT, KEYWORD_LIST, TIPS_OF_ACTION_CLASSIFICATION, DOMAIN_KNOWLEDGE, NUMBER_OF_GROUPS
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

