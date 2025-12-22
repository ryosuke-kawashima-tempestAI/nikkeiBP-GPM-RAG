import os

# -----------------------------
# Configuration
# -----------------------------
APIKEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = APIKEY
TARGET_PATH = "./target/ma_welding_llds.xlsx"
# RAG Mode
PDF_URL = "https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r05/pdf/00zentai.pdf"
PDF_PATH = "./documents/nikkeiBP_day5.pdf"
EXCEL_PATH = "./documents/gpm_tips.xlsx"
PROMPT_PATH = "./prompts/nikkeiBP_mermaid.md"
GRAPH_PATH = "./knowledge_graphs/NikkeiBP_meronymy_hyponymy.mmd"
# Persist vector DB to avoid recomputation across runs
PERSIST_DIR = "domain_db"
# Retrieval defaults
TOP_K = 10
RELEVANCE_THRESHOLD = 0.1  # larger (e.g., 0.3–0.5) = stricter filtering

# -----------------------------
# GPM Generation Rules
# -----------------------------
SYSTEM_PROMPT = """
# Engineering Process Actions Categorization and Grouping

## Role

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a **Car Welding** process, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the **Car Welding** process.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed sequential logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

"""
# Roughly as many groups as the one by the human knowledge engineer
NUMBER_OF_GROUPS = 45
KEYWORD_LIST = """
300dフロントピラー
基準3a
基準3b
基準3c
300Dトルーフ
トリムライン
120D
SQ101
W/Hアウターパネル
32Dセンターフロア
部品460B ラダーAssy
ロッカーインナRr
M治具基準SQ101
固定用W副基準
"""

# General Strategic Knowledge
TIPS_OF_ACTION_CLASSIFICATION = """
- アクションを類別する際にアクションに含まれるキーワードとなる名詞に着目して、同じあるいは似た意味の名詞を含むアクションをもとに分類する。
- 次にキーワードに対する動作つまり動詞の類似性に着目してアクションを類別する。
- 複数個前に行ったアクションの結果が後のアクションの結果に響くことがあるので、前後のアクションの情報を参照する必要がある。
- アクションを類別する際にInputとOutputが類似しているかを考慮するべき。
- アクションのラベルが違う場合でもIntentionが類似している場合は同じグループに入れる。
- アクションが生成する入力と出力に含まれるキーワードの意味の類似性をもとにGPMのクラスを生成する。
- GPMのクラスを生成する際に、元となるLLDの動詞とGPMの動詞を**類似**させる。
- GPMのクラスを生成する際に、元となるLLDのアクションの目的語とGPMのクラスの目的語を**類似**させる。
"""

# Specific Domain Knowledge
DOMAIN_KNOWLEDGE = """
### Domain Rules

- 300Dフロントピラーは組付け精度を決定する部位である。
- 基準3aは300Dフロントピラーの基準位置を決定する。
- 基準3bは300Dフロントピラーの基準位置を決定する。
- 基準3cは300Dフロントピラーの基準位置を決定する。
- 300Dトルーフは組付け精度を決定する部位である。
- トリムラインは300Dトルーフを含めた全体の剛性を確保する。
- 120Dは組付け精度を決定する部位である。
- SQ101は120Dの組付け精度を決定する基準である。
- W/Hアウターパネルの剛性は部品の単体制度に影響を与える。
- 32Dセンターフロアは部品の単体精度に影響を与える。
- 部品460B ラダーAssyは部品の単体精度に影響を与える。
- ロッカーインナRrは部品460B ラダーAssyの組付け精度が低い場合に外出する部位である。
- 固定用W副基準は300Dトルーフ単品を固定するための基準である。
- 溶接工程の部品の精度の不良について(1)基準位置が悪くて変形する(2)治具の締め付けが悪くて変形する(3)プレス成型の形状が寸法通りでない、の3通りの要因が考えられる。

### Domain Examples

Example 1:
    LLD Actions: 
        - 選択されたサブプロセスに対して隙間の解消案を立案する
            - ID: 55
            - Input: 選択したサブプロセス：300Dトルーフの単体精度不良
            - Output: 300Dトルーフのパネル形状を変更する
        - 300Dトルーフ単品の形状変更の位置を決める
            - ID: 56
            - Input: 300Dトルーフのパネル形状を変更する
            - Output: 300Dトルーフの形状変更位置：トリムライン
        - 300Dトルーフ単品の形状変更の形を決める
            - ID: 57
            - Input: 300Dトルーフの形状変更位置：トリムライン
            - Output: トリムライン形状変更案
    GPM Answers:
        GPM Action 1: 着目すべき原因を選定する
            - Refrence LLD ID: 55
            - Input: 300Dトルーフの単体精度不良
            - Output: 300Dトルーフのパネル形状を変更する
            - PartOf: Another GPM Action
        GPM Action 2: 原因と推定される部品の位置を決定する
            - Refrence LLD ID: 56
            - Input: 原因と推定される部品
            - Output: 部品の変更先の位置
            - PartOf: GPM Action 1
        GPM Action 3: 原因とされる部品の形状を決定する
            - Refrence LLD ID: 57
            - Input: 原因とされる部品や基準部位
            - Output: 部品の形状変更案
            - PartOf: GPM Action 1
    Reasoning:
        - まずはLLDの動詞とGPMの動詞を類似させる
        - 次にLLDの目的語とGPMの目的語を類似させる
        - 300Dトルーフ単品の形状変更の位置や300Dトルーフ単品の形状変更の形は隙間の解消案に含まれるので、GPM Action 2とGPM Action 3はGPM Action 1のPartOfである。

"""

EVALUATION_CRITERIA = """
- The input of a LLD action is semantially similar to the output of the previous action.
- The output of a LLD action is semantially similar to the input of the next action.
- The input of a GPM action is semantially similar to the output of the previous GPM action of the same PartOf relationship.
- The output of a GPM action is semantially similar to the input of the next GPM action of the same PartOf relationship.

- You need to check whether the sequential order of LLD actions are preserved in the GPM actions.
    - You need to mention the reason of why the sequential order of LLD actions should be preserved in the corresponding GPM classes.
    - If the sequential order of LLD does not have to be preseved, you need to point out the reason to justify this.
"""
