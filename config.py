import os

# -----------------------------
# Configuration
# -----------------------------
APIKEY = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = APIKEY
PDF_URL = "https://www.soumu.go.jp/johotsusintokei/whitepaper/ja/r05/pdf/00zentai.pdf"
PDF_PATH = "./documents/nikkeiBP_day5.pdf"
EXCEL_PATH = "./documents/gpm_tips.xlsx"
PROMPT_PATH = "./prompts/nikkeiBP_mermaid.md"
TARGET_PATH = "./target/nikkeiBP_LLDs.xlsx"
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

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a sandwitch factory, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the sandwich factory.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

"""
NUMBER_OF_GROUPS = 30
KEYWORD_LIST = """
- 改善案
- 改善対象
- 生産ライン
- サイクルタイム
- 搬送人数
- ポイント
- コスト
- バッファサイズ
- 初期在庫
- 生産量
- シミュレーション
"""

TIPS_OF_ACTION_CLASSIFICATION = """
- アクションを類別する際にアクションに含まれるキーワードとなる名詞に着目して、同じあるいは似た意味の名詞を含むアクションをもとに分類する。
- 次にキーワードに対する動作つまり動詞の類似性に着目してアクションを類別する。
- 複数個前に行ったアクションの結果が後のアクションの結果に響くことがあるので、前後のアクションの情報を参照する必要がある。
- アクションを類別する際にInputとOutputが類似しているかを考慮するべき。
- アクションのラベルが違う場合でもIntentionが類似している場合は同じグループに入れる。
"""

DOMAIN_KNOWLEDGE = """
- CTとコストはトレードオフの関係にある。コストを改善するとCTは悪化し、CTを改善するとコストは悪化する。
- 搬送人数とコストは比例の関係にある。つまり搬送人数とコストはトレードオフの関係にある。
- サイクルタイム(CT) を操作する動作には、(1)最適値を模索するためにランダムに指定する場合 (2) 減少させることで生産量を向上させる場合 (3) 増加させることでコストを低下させる場合の3つがある。
- ポイントとはパフォーマンスのことである。
- EAZY GO はシミュレーションソフトである。
- 出来高と生産量はほぼ同じ意味である。
- バッファサイズが大きいほどコストが増大する。
- CTを下げるとポイントは上昇する。
- 搬送人数とポイントは比例の関係にある。
"""
