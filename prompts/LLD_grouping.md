# Engineering Process Actions Categorization and Grouping

## Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a **Car Welding** process, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the **Car Welding** process.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed sequential logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

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
- [ ] This type of classification includes about **{NUMBER_OF_TOP}** groups.
- [ ] You should clarify the reason of the classification.

### Step 3: Classify actions by more specific classification

- [ ] Some groups should be further classified into subgroups **recursively**.
  - [ ] This process should be repeated until all actions are assigned to a group.
  - [ ] Some LLD actions are not assigned to more specific classification, while others are assigned to more specific classification.
  - [ ] This type of classification includes about **{NUMBER_FOR_EACH_CONTAINER}** actions for each group.
- [ ] Source and Knowldge of action classification should be listed not only from **keyword list**, **tips of action classification** and **domain knowledge** but also from your knowledge.
- [ ] You should clarify the reason of the classification.

### Step 4: Assign the GPM ID and Class Name to every action

- [ ] Assign the GPM ID to every action.
- [ ] The ID should start from 1 and be consecutive.
- [ ] Assign the Class Name to every action.
- [ ] The Class Name should be **operations** of engineering process in Japanese.
  - [ ] You should also reconstruct the Input and Output of every GPM actions.
  - [ ] You should also reconstruct the Intention of every GPM actions.
- [ ] You should clarify the reason of construction of every GPM actions and their elements.

### Step 5: Evaluate the classification of LLD actions and the knowledge of action classification

- [ ] Based on the provided information and knowledge, evaluate the classification of LLD actions and the knowledge of action classification.
  - [ ] If you find actions which are not assigned any group name, you should assign a group name to them.
  - [ ] You must not make blanks on **ClassName**.
- [ ] Then, refine and improve the categorization of LLD actions into GPM classes, referring to the **Sources** section.

## Format

- [ ] List all the actions in a table with the following columns.

  - ClassID
    - Integer. It should start from 1 and be consecutive.
  - ClassificationReason
    - String. It should be the reason of the classification.
  - ClassInput
    - String. It should be the input of the action.
  - ClassName
    - String. The name should be **operations** of engineering process in Japanese.
  - ClassOutput
    - String. It should be the output of the action.
  - ClassIntention
    - String. It should be the reason of the classification.
  - PartOf
    - Integer. It should be the ID of the group that the action belongs to.
  - PartOfReason
    - String. It should be the reason of the classification.

## Constraints

- [ ] The number of groups should be about **{NUMBER_OF_GROUPS}**.
- [ ] If there are actions that are not assigned to any group, you need to create a new group for them.
- [ ] You must not make blanks on **ClassName**.
- [ ] There should be no actions left unassigned.
- [ ] You should assign the ID and name of the group to **every** action.
