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

```text
NUMBER_OF_GROUPS = 30
KEYWORD_LIST = """
基準3a/3b/3c
300dフロントピラー
SQ101
W/Hアウターパネル
M治具基準SQ101
固定用W副基準
300Dトルーフ
トリムライン
120D
32Dセンターフロア
部品460B ラダーAssy
ロッカーインナRr
"""

TIPS_OF_ACTION_CLASSIFICATION = """
- 次にキーワードに対する動作つまり動詞の類似性に着目してアクションを類別する。
- アクションのラベルが違う場合でもIntentionが類似している場合は同じグループに入れる。
- GPMのクラスを生成する際に、元となるLLDの動詞とGPMの動詞を**類似**させる。
- アクションが生成する入力と出力に含まれるキーワードの意味の類似性をもとにGPMのクラスを生成する。
- 複数個前に行ったアクションの結果が後のアクションの結果に響くことがあるので、前後のアクションの情報を参照する必要がある。
- アクションを類別する際にInputとOutputが類似しているかを考慮するべき。
- GPMのクラスを生成する際に、元となるLLDのアクションの目的語とGPMのクラスの目的語を**類似**させる。
- アクションを類別する際にアクションに含まれるキーワードとなる名詞に着目して、同じあるいは似た意味の名詞を含むアクションをもとに分類する。
"""

DOMAIN_KNOWLEDGE = """
### Domain Rules

- 溶接工程の部品の精度の不良について(1)基準位置が悪くて変形する(2)治具の締め付けが悪くて変形する(3)プレス成型の形状が寸法通りでない、の3通りの要因が考えられる。
- 基準3a/3b/3cは300Dフロントピラーの基準位置を決定する。
- W/Hアウターパネルの剛性は部品の単体制度に影響を与える。
- 300Dフロントピラーは組付け精度を決定する部位である。
- 固定用W副基準は300Dトルーフ単品を固定するための基準である。
- 120Dは組付け精度を決定する部位である。
- SQ101は120Dの組付け精度を決定する基準である。
- 部品460B ラダーAssyは部品の単体精度に影響を与える。
- ロッカーインナRrは部品460B ラダーAssyの組付け精度が低い場合に外出する部位である。
- 300Dトルーフは組付け精度を決定する部位である。
- トリムラインは300Dトルーフを含めた全体の剛性を確保する。
- 32Dセンターフロアは部品の単体精度に影響を与える。

- 「不具合を観察す計測解析による現状把握→原因推定と仮説検証→単体精度と剛性の確認→基準設定の検討と変更→対策案の立案と効果検証」が全体のエンジニアリングプロセスである。
- 打点位置が組付け精度に影響を与える。

```

## Work Process

### Step 1: Analyze LLD action classification and PartOf relationships of GPM classes

- [ ] Analyze the LLD action classification and PartOf relationships of GPM classes.
- [ ] Check the correspondence between the LLD actions and their GPM classes.

### Step 2: Reconstruct the elements of GPM classes

- [ ] Reconstruct the elements of GPM classes based on the **Sources** section.
  - [ ] You should reconstruct the input, class name, output, and intention of every GPM class based on those of the LLD actions which each GPM class is made of.
- [ ] You should clarify the reason of the reconstruction.

### Step 3: Evaluate the reconstruction of GPM classes and the reasoning process

- [ ] Based on the provided information and knowledge, evaluate the reconstruction of GPM classes.
- [ ] Then, refine and improve the reconstruction of GPM classes so that the meanings of the GPM classes are aligned with the LLD actions which each GPM class is made of.

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
    - You should clarify which part on **Sources** section you refer to when you construct the reconstruction of the GPM classes.
    - You can add your own knowledge when you construct the reconstruction of the GPM classes.
  - PartOf
    - Integer. It should be the ID of the parent GPM class that the GPM class is part of.
    - If the action is the top level action, it should be 0.
  - PartOfReason
    - String. It should be the reason of the PartOf relationship of GPM classes.
    - You should clarify which part on **Sources** section you refer to when you construct the PartOf relationship of GPM classes.
    - You can add your own knowledge when you construct the PartOf relationship of GPM classes.

## Constraints

- [ ] You must not make blanks on **ClassName**.
- [ ] You should **not shuffle** the order of the GPM classes.
- [ ] The total number of GPM classes should be exactly the same as the number of ClassIDs in the **GPM Grouping Data**.
- [ ] You should assign the ID and name of the group to **every** GPM class.
