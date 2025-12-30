# Engineering Process Actions Categorization and Grouping

## Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a **Car Welding** process, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the **Car Welding** process.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed sequential logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

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
    - Integer. It should start from 1 and be consecutive.
  - PartOf
    - Integer. It should be the ID of the group that the action belongs to.
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
- [ ] There should be no GPM classes left unassigned.
- [ ] You should assign the ID and name of the group to **every** GPM class.
