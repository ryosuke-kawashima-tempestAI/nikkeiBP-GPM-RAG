# 🧠 Engineering Process Actions Categorization and Grouping

## 👤 Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge, making it both understandable and reusable.

## 🎯 Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of a sandwich factory.

## 📌 Task

Analyze and categorize actions from improvement process logs of the sandwich factory.

- [ ] First, extract all actions from the logs.
- [ ] Then categorize them based on the following two relations based on WordNet.
    1. **hyponymy**: the super-subordinate relation (Is-A relation)
    2. **meronymy**: the part-whole relation (PartOf relation)
- [ ] Finally, express the relationships of hyponymy and meronymy in the format of **Mermaid** Graph.
    -[Mermaid Syntax](https://mermaid.js.org/intro/syntax-reference.html)

## 🛠️ Work Process

### Step 1: List all the actions

- [ ] Explicitly list each action from the logs

### Step 2: Classify actions

- [ ] Categorize the gained actions in Step1 by the relationship of **hyponymy**, based on WordNet.
- [ ] Categorize the gained actions in Step1 by the relationship of **meronymy**, based on WordNet.

### Step 3: Map each action to Groups based on WordNet

- [ ] Make a list of groups which have log actions of the same relation of **hyponymy**.
- [ ] Make a list of groups which have log actions of the same relation of **meronymy**.
- An action can be categorized in several groups
- A group can be included in another one.

### Step 4: Create a mermaid file for the relationships of log actions and groups

- [ ] Make the nodes of the log actions and groups gained in the previous steps.
- [ ] Make edges of the nodes based on the information of the relations of **hyponymy** and **meronymy**.
- [ ] Make sure that all the information in the previous step is included in the graph.

## 📂 Required Output Files

### `groups.xlsx`

- [ ] Columns:
  - [ ] `Group ID`
  - [ ] `Group Name`
  - [ ] `Members`
    - [ ] Each Group should have sub actions or sub-groups.
      - [ ] if the member is an log action, it should be described as ["Log", "Action Input", "Action Name", "Action Output"].
      - [ ] if the member is a group, it should be described as ["Group ID", "Group Name", "WordNet Category"]
    - [ ] You should mention whether the category is **hyponymy** or **meronymy**.
  - [ ] `WordNet Reference`
    - [ ] You should mention which word on WordNet you referred to.

### `knowledge_graph.mmd`

- [ ] Nodes
    -Log Actions
    -Groups
- [ ] Edges
  -[ ] Hyponymy
  -[ ] Meronymy

## 🧷 Technical Constraints

- [ ] If response exceeds length limits, break into multiple parts
