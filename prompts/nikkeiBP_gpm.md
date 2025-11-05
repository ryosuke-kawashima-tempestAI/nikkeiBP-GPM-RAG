# 🧠 GPT Prompt in Markdown Task Format

## 👤 Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a sandwitch factory, making it both understandable and reusable.

## 🎯 Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the sandwich factory.

## 📌 Task

- [ ] Based on the provided examples, analyze and categorize actions from improvement process logs of the sandwich factory.
- [ ] First, extract all actions from the logs.
- [ ] Then categorize them based on their similarities.

## 📏 Rules

### General Classification

- Study the provided examples to understand the expected classification methodology.
- When comparing actions, prioritize their **names**. Even with different proper nouns (e.g., machine names), if the actions are conceptually the same, categorize them together.
- Actions repeated in different logs should be grouped together **if similar**.
- Each action’s **input** and **output** must be consistent with those of other actions within the same category.
- Consider **intent** as critical. Even if two actions have the same name, if their intent differs significantly, categorize them separately.
- The task has **two main steps**: extraction and classification.
- List all actions under the same type together, with the **log number marked in brackets** (e.g., `[Log 1]`).
- All classification output must be in **Japanese**.
- Categorize actions into **classes** with a unique:
  - [ ] Japanese name
  - [ ] English name

### Class Naming Rules

- Action names should be descriptive sentences capturing the **essence** of all grouped actions.
- Replace specific names (components, machines, etc.) with **generic/common nouns**.
- Sentence format:  
  - Japanese: 「〇〇の〇〇を〇〇する」  
  - English: "Perform [specific operation] on [specific part] of [specific object]"

### Engineering Cycle

- An engineering cycle is a sequence of five steps that together represent a complete iteration of the engineering process:

1. Problem Definition
  – The process of identifying the scope of issues within the process and determining which problems need to be addressed.
2. Information Collection/Analysis
  – The process of gathering data related to the issues identified during the problem definition stage and analyzing the collected data to derive insights.
3. Hypothesis Generation
  –  The process of formulating hypotheses to address the issues defined in the problem definition stage, based on insights gained during the information collection and analysis stage.
4. Information Evaluation/Selection
  – The process of assessing each hypothesis to determine whether it accurately reflects the real-world problem and identifying the most suitable approach to resolve the issues defined in the problem definition stage.
5. Execution
  – The process of implementing the proposed solutions from the information evaluation and selection stage to address the identified issues.

- While engineering cycles are typically executed in the order described above, certain situations may require a different sequence.

### Subaction

- A subaction is an action that forms part of a parent action, where the parent action consists of a sequence of actions, including that subaction.
- The **input** of a parent action should match the **input** of its **first** subaction.
- The **output** of a parent action should match the **output** of its **last** subaction.

#### Example of Parent–Subaction Relationship

Actions:

- Action1:  
  `input = "no input"`, `Action = "特定の機械を観察する"`, `output = "観察結果"`  
- Action2:  
  `input = "no input"`, `Action = "特定の機械を選択する"`, `output = "マシン2"`  
- Action3:  
  `input = "マシン2"`, `Action = "マシン2を観察する"`, `output = "マシン2の観察結果"`

Relationship:

- Action1 is the parent action.  
- Action2 and Action3 are its subactions, executed in the order: Action2 → Action3.  
- **First subaction**: Action2 has the corresponding **input** as the parent action (Action1).  
- **Last subaction**: Action3 has the corresponding **output** as the parent action (Action1).  

### Special Cases

- [ ] Actions that do **not fit any class** must be listed separately at the end.
- [ ] Every single action must be listed, even if duplicated across or within logs.
- [ ] No action can be skipped or assumed.
- [ ] After listing, ensure each action is linked to a class or separately labeled as uncategorized.

## 💡 Tips

- Log1 contains **7 actions**
- Log2 contains **23 actions**
- Log3 contains **28 actions**
- Total: **58 actions**
- [ ] Duplicate names in the same log must be listed as separate actions.

## 🛠️ Work Process

### Step 1: List all the actions

- [ ] Explicitly list each action from the logs
- [ ] Treat actions with the same name as unique if they appear multiple times
- [ ] Categorize each action according to the five stages of the Engineering Cycle.
- [ ] Determine the parent–subaction relationships and the order of subactions within each parent.

### Step 2: Classify actions

- [ ] Create grouped classes according to similarity and intent
- [ ] Categorize each class according to the five stages of the Engineering Cycle.
  - [ ] if it cannot be assigned to any of the five categories, classify it as **Others**.
- [ ] Assign unique names to each class in Japanese and English

### Step 3: Map each action to a class

- [ ] Ensure all the actions are included
- [ ] For any action that cannot be categorized, mark as separate (but not as its own class)

## 🧪 Example Class (from learning data)

Descriptions of the process follow the specific format:
["Log", "Action Input", "Action Name", "Action Output", "Action Intention"]

### Class 01: 現状を確認する / "Check Current State"

- [“2”, “no input”, “現状の出来高を調べる”, “タマゴサンドラインの出来高が50％以下と低い”, “no intention”]
- [“4”, “M2:45,M3:45”, “改善前の出来高を調べる”, “出来高:55.33”, “効果を知りたい”]

### Class 02: シミュレーションを実行する / "Run Simulation"

- [“1”, “no input”, “シミュレーションで生産量とコストを確認する”, “コスト：440,生産量：77.1”, “no intention”]
- [“3”, “M2,M3”, “M2とM3のCTの変更可能範囲を調べる”, “M2:45-55,M3:45-55”, “no intention”]
- [“4”, “M2,M3”, “コストを調べる”, “コスト:69.17”, “no intention”]

## 📂 Required Output Files

### 1. `classes.xlsx`

- [ ] Columns:
  - [ ] `Class_ID`
  - [ ] `Class_Japanese`
  - [ ] `Class_English`
  - [ ] `Log Reference (Action IDs)`
    - [ ] References are described as ["Log", "Action Input", "Action Name", "Action Output"].
- [ ] Ensure all class IDs are **unique**
- [ ] Do not duplicate class names

### 2. `logs.xlsx`

- [ ] Based on: `LLD_nikkei_first.xlsx`
- [ ] Add new column: 
  - [ ] `Class_ID`
  - [ ] `Engineering_Cycle`
  - [ ] `Parent Action`
    - [ ] The parent action should be represented as ["Action ID", "Action Name"].
    - [ ] If the action has no parent action. Label it as **no parent**.
  - [ ] `Subactions`
    - [ ] For actions with subactions, create an ordered list of subaction names.
    - [ ] If an action has no subactions, label it as **no subaction**.

## 🧷 Technical Constraints

- [ ] IDs and Logs must be integers
- [ ] If response exceeds length limits, break into multiple parts
