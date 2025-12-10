import os

# -----------------------------
# Configuration
# -----------------------------
APIKEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = APIKEY
TARGET_PATH = "./target/learning_factory_llds.xlsx"
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

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a **LEGO cars** factory, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the **LEGO cars** factory.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed sequential logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

"""
NUMBER_OF_GROUPS = 30
KEYWORD_LIST = """
- ロボット
- サイクルタイム (CT)
- マシン
    - マシン１
    - マシン２
    - マシン３
- パレット
- ルーフ部品
- ライン
- 観測結果
- 短縮方針
- 完成品
- タイヤ
"""

# General Strategic Knowledge
TIPS_OF_ACTION_CLASSIFICATION = """
- アクションを類別する際にアクションに含まれるキーワードとなる名詞に着目して、同じあるいは似た意味の名詞を含むアクションをもとに分類する。
- 次にキーワードに対する動作つまり動詞の類似性に着目してアクションを類別する。
- 複数個前に行ったアクションの結果が後のアクションの結果に響くことがあるので、前後のアクションの情報を参照する必要がある。
- アクションを類別する際にInputとOutputが類似しているかを考慮するべき。
- アクションのラベルが違う場合でもIntentionが類似している場合は同じグループに入れる。
- アクションが生成する入力と出力に含まれるキーワードの意味の類似性をもとにGPMのクラスを生成する。
"""

# Specific Domain Knowledge
DOMAIN_KNOWLEDGE = """
### Domain Rules

### Domain Examples

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
