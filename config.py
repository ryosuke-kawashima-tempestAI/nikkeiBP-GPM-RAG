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

GUIDELINE_RULES = """

"""

FEW_SHOT_EXAMPLES = [
    {

    }
]

