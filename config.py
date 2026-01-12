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

You are a **Knowledge Engineer**, responsible for designing models that capture and structure process knowledge at a **LEGO car factory** process, making it both understandable and reusable.

## Objective

Summarize the problem-solving processes to create a representative, generic model of the improvement process of the **LEGO car factory** process.

## Context

- LLD is an abbreaviation for Low Level Descriptions, which are detailed sequential logs of actions taken during the process.
- GPM is an abbreviation for General Process Model, which is a representative, generic model of the process gained from several LLDs.

"""
# Roughly as many groups as the one by the human knowledge engineer
# parameters for the top-down approach
NUMBER_OF_TOP = 5
NUMBER_OF_GROUPS = 25
KEYWORD_LIST = """
- マシン１
- マシン２
- マシン３
- IoT Data View
- fastSUITE
"""

# General Strategic Knowledge
TIPS_OF_ACTION_CLASSIFICATION = """
- GPMの包含関係において上位に来るアクションとして下位のアクションに比べて一般的あるいは抽象的なアクションを設定する。
- 次にキーワードに対する動作つまり動詞の類似性に着目してアクションを類別する。
- アクションのラベルが違う場合でもIntentionが類似している場合は同じグループに入れる。
- GPMのクラスを生成する際に、元となるLLDの動詞とGPMの動詞を**類似**させる。
- アクションが生成する入力と出力に含まれるキーワードの意味の類似性をもとにGPMのクラスを生成する。
- 複数個前に行ったアクションの結果が後のアクションの結果に響くことがあるので、前後のアクションの情報を参照する必要がある。
- アクションを類別する際にInputとOutputが類似しているかを考慮するべき。
- GPMのクラスを生成する際に、元となるLLDのアクションの目的語とGPMのクラスの目的語を**類似**させる。
- アクションを類別する際にアクションに含まれるキーワードとなる名詞に着目して、同じあるいは似た意味の名詞を含むアクションをもとに分類する。
"""

# Specific Domain Knowledge
DOMAIN_KNOWLEDGE = """
### Domain Rules

- マシン１は6軸ロボットである．
- マシン２はスカラロボットである．
- マシン３は直行ロボットである．
- IoT Data ViewはラインのIoTデータを表・グラフ形式で表示する．
- サイクルタイム：製品１個が，１つの工程を終えるのに要する時間
- 自動化工場を模擬した設備であるラーニングファクトリーを対象に，サイクルタイムを短縮するための案を導出する．
- 実際にラーニングファクトリーが稼働している様子を見て，サイクルタイムを遅くしている原因の特定及びその解決策を検討する．
- 大きく3つのマシンに分かれる．
- 各マシンにロボットが1つ含まれている．
- ロボットは，ベルトコンベアで運搬されるパレット上で組立/検査作業を実施
- コントローラが，生産ラインの動きを制御をしている．
- ロボット・コントローラ：　ロボットの軌跡，速さ，起動タイミング等のロボットの動きを制御
- プログラマブル・ロジック・コントローラ（PLC），アクチュエータ・コントローラが機械の変位やベルトコンベアの速さ等のロボット以外（ベルトコンベアや，その他のアクチュエータなど）の機械の動きを制御
- fastSUITEはコントローラのI/O信号を取得して，実ラインと同期して動くシミュレーションソフトである．
- 本ラーニングファクトリーでは，サイクルタイムを2種類の方法で表示可能である(1. 各マシンのモニタ　に表示 2. IoT Data View に表示)

### Domain Examples

- サイクルタイムの確認は生産ラインの現状把握を行うための行為の一つである。

"""

ExampleTemplate = """
Example 1:
    LLD Actions: 
            - 選択されたサブプロセスに対して隙間の解消案を立案する
                - ID: 55
                - Input: 選択したサブプロセス：300Dトルーフの単体精度不良
                - Output: 300Dトルーフのパネル形状を変更する
        GPM Answers:
            GPM Action 1: 着目すべき原因を選定する
                - Refrence LLD ID: 55
                - Input: 300Dトルーフの単体精度不良
                - Output: 300Dトルーフのパネル形状を変更する
                - PartOf: Another GPM Action
        Reasoning:
            - 
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

KEYWORD_TEPMPLATE = """
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
