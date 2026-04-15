<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>すべてを喰らう。永遠に進化する。あなたはただ話すだけ。</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat&cache_seconds=0" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#クイックスタート">クイックスタート</a> · <a href="#日常のフロー">日常のフロー</a> · <a href="#アーキテクチャ">アーキテクチャ</a> · <a href="#統合">統合</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · <a href="README_zh.md">中文</a> · 日本語
</p>

---

LangChain。LangGraph。CrewAI。DSPy。Hermes。毎月、新しいフレームワークが「これこそ本命」だと約束してくる。あなたは、何かを作ることより、ツールを選ぶことに多くの時間を費やしている。

フレームワークだけではない。論文、API、ベストプラクティス、毎日すべてが更新される。ノートアプリには 500 件、最後に整理したのは三ヶ月前、たぶんもっと前。あの丁寧に書いたノートは腐っていく。三週間前の API？バージョンが変わった。**誰も、代わりにチェックしてくれない。**

あなたの AI は先週の決定も覚えていない。新しい会話のたびに、毎回ゼロから。

<br>

別の生き方を想像してほしい。あなたはただ普通に話すだけ。整理もせず、比較もせず、論文を追わず、プロジェクトを説明し直さない。半年後、あなたの AI は誰の AI よりも鋭くなっている——自分であなたの分野の最新の仕事を喰らい、自分の盲点を見つけて埋め、真ではなくなった古い知識を捨て、足りなくなった運用ルールを自分で書き直している。

<h3 align="center">これが Myco です。</h3>

---

## Myco とは

教えたことを決して忘れない AI を想像してみてください。あなたが投げた論文、決定、「あれ間違ってたな」の一言——すべてを喰らう AI を。自分の理解が古くなったと気づけば、自分で直す AI を。今日の思いつきを、三ヶ月前のあなたが半分忘れたノートとつなぎ、あなたが覚えていなくていい AI を。

それが Myco です。

Myco は **あなたの AI エージェントの生きた認知基層** — エージェントのもう半身として、あなたと一緒に喰らい、消化し、守り、育つものです。記憶データベースではない、エージェントランタイムでもない、スキルフレームワークでもない。エージェントのすぐ隣で動き、エージェントを「記憶する相棒」に変えます。

### 五つの原則の上に立つ

- **エージェント専用。** あなたは Myco を閲覧しない。あなたはエージェントと話す；エージェントが Myco を読む。すべての表面——`_canon.yaml`、notes、doctrine、boot brief——はエージェントが読むための一次資料であり、人が読むドキュメントではない。
- **万物を吞噬。** 取り込みにフィルタなし。決定、摩擦、論文、ログ、半熟の思いつき——何でも raw のまま捕らえる。形は後で整える。信号を取り逃がす代償は、取り込みすぎる代償より常に高い。
- **自己進化する形。** canon schema、lint 次元、契約そのもの——すべて一等可変オブジェクト。凍った基層は死んだ基層。進化はガバナンス（craft → PR → bump）を通り、ドリフトでは通らない。
- **「最終版」は存在しない。** `integrated` は状態であって終点ではない。今日消化したノートは、明日 context が鋭くなれば再消化できる。省察は家事ではなく、鼓動。
- **菌糸ネットワーク。** note、canon フィールド、doctrine ページは互いに辿れるようにリンクされる。孤児は死んだ組織。このグラフこそエージェントが知識を読む方法——なので常に生かしておく必要がある。

### 三つの役割、連携する

**あなた** — 方向を決める。何をすべきか言う。CLI を覚えない、ファイルを整理しない、次のセッションで自分のプロジェクトを説明し直さない。

**エージェント** — 知性をもたらす。あなたの言葉を読み、Myco を読み、verb を選び、書き戻す。

**Myco** — 代謝を回す。あなたの発話の合間に、**hunger**（何が足りない？）、**eat**（raw を取り込む）、**reflect / digest / distill**（raw → 構造化 → doctrine）、**immune** でドリフト防止、**propagate** で学びをプロジェクト間に広げる。12 個の verb、1 つの manifest、2 つの面：観察のための CLI、エージェントが駆動する MCP。

> **kernel は安定、substrate は可変。** `pip install` は kernel をリリース版でロックする。substrate（`_canon.yaml`、`notes/`、`docs/primordia/`）は 12 個の MCP verb によって日々進化する。kernel の進化は upstream のガバナンス。

## クイックスタート

```bash
pip install 'myco[mcp]'
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

3 つのコンソールスクリプトが PATH に載ります：

- `myco` — 12 verb の CLI。
- `mcp-server-myco` — 汎用 MCP stdio ランチャー。どの host にも挿せます。
- `myco-install` — 主要 7 つの MCP host に 1 コマンドで導入。

**Claude Code / Cowork** は公式プラグインで一括導入（MCP + hooks + slash skills）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**その他の MCP host** も 1 コマンドで済みます：

```bash
myco-install cursor        # または: claude-desktop / windsurf / zed / vscode / openclaw
```

あるいは汎用スニペットを host の設定ファイルに貼り付け——`mcpServers` ファミリー（Claude Desktop、Cursor、Windsurf、Cline、Roo Code、Gemini CLI、Qwen Code、JetBrains AI、Augment Code、AiderDesk）で動作します：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

設定スキーマが異なる 8 つの host——VS Code Copilot（`servers`）、Zed（`context_servers`）、OpenClaw（`mcp.servers` + CLI）、OpenHands（TOML）、OpenCode / Kilo Code（`mcp`）、Codex CLI（TOML）、Goose（YAML `extensions`）、Continue（YAML ブロック）、Warp（`mcp_servers`）——は、それぞれ正確なスニペットを [`docs/INSTALL.md`](docs/INSTALL.md) に収録。Python フレームワーク adapter（LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK）も同ページに。

ライブラリ組み込み：

```python
from myco.mcp import build_server
build_server().run()                   # stdio（デフォルト）
build_server().run(transport="sse")    # HTTP SSE
```

コントリビュートまたは fork する場合は editable install：

```bash
git clone https://github.com/Battam1111/Myco && cd Myco
pip install -e '.[dev,mcp]'
```

## 日常のフロー

エージェントが駆動するので、あなたは何も覚える必要はありません。12 個の verb は 5 つのサブシステムに分類されます：

| サブシステム | Verbs | 何が起こるか |
|---|---|---|
| **Genesis** | `genesis` | 新しい substrate をブートストラップ。 |
| **Ingestion** | `hunger` · `sense` · `forage` · `eat` | 今何が必要か；キーワード検索；取り込み可能なファイルの列挙；raw note を記録。 |
| **Digestion** | `reflect` · `digest` · `distill` | raw → integrated；integrated → doctrine へ蒸留。 |
| **Circulation** | `perfuse` · `propagate` | 参照グラフの健全性；下流 substrate への発行。 |
| **Homeostasis** | `immune` | 4 カテゴリ / 8 次元の一貫性 lint（`--fix` 対応）。 |
| *（meta）* | `session-end` | `reflect` + `immune --fix`；PreCompact により自動発火。 |

CLI：`myco VERB`——グローバル flag（`--project-dir`、`--json`、`--exit-on`）は verb の **前** に置きます。MCP：1 verb につき 1 tool、パラメータは `src/myco/surface/manifest.yaml`（CLI と MCP 共通の SSoT）から機械的に派生。

## アーキテクチャ

```
あなた ──▶ エージェント ──▶ Myco substrate
                             ├── _canon.yaml        SSoT：identity · 書き込み面 · lint 方針
                             ├── MYCO.md            エージェント入口ページ（R1）
                             ├── notes/{raw,integrated,distilled}/
                             ├── docs/architecture/ L0 vision · L1 contract · L2 doctrine · L3 impl
                             ├── src/myco/          genesis · ingestion · digestion · circulation · homeostasis · surface
                             └── .claude/hooks/     SessionStart → hunger · PreCompact → session-end
```

ハード契約 7 条（R1–R7）はフック・免疫システム・エージェントの規律の三者によって強制されます。全文：[`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## クロスプラットフォーム強制メカニズム — どのホストも置き去りにしない

R1–R7 は Claude Code / Cowork では hook が強制。それ以外の host — Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands — では強制は **MCP server 自体** に組み込まれています：

- **初期化指示。** `initialize` 時に、すべての host に短い R1–R7 サマリーと [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md) へのリンクが届きます。instructions を読む Agent は、最初の tool 呼び出し前に契約を見る。
- **`substrate_pulse` サイドカー。** すべての tool 応答は `substrate_pulse` フィールドを含み、現在の `contract_version`、`substrate_id`、および R1（hunger 未コール）→ R3（sense before assert）へと昇格するルールヒントを運ぶ。サーバサイドからの push であり、Agent が契約を忘れることはできない。

host 側設定ゼロ、すべての MCP クライアントで動作します。

## 統合

- **Claude Code / Cowork** —— `/plugin marketplace add Battam1111/Myco` → `/plugin install myco@myco`。または手動で `.claude/` をコピー。
- **任意の MCP ホスト** —— 7 つの主要ホストは `myco-install <client>`、それ以外は `mcp-server-myco` stdio。正確な per-host スニペットは [`docs/INSTALL.md`](docs/INSTALL.md)。
- **Python エージェントフレームワーク** —— LangChain · CrewAI · DSPy · Smolagents · Agno · PraisonAI · Microsoft Agent Framework · Claude Agent SDK はすべて `StdioServerParameters(command="mcp-server-myco")` で Myco を消費。
- **下流 substrate** —— `myco propagate` が発行；adapter は `myco.symbionts` に。

## もっと知る

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

コントリビュート：`pip install -e ".[dev]"`；アーキテクチャに関わる変更は [`docs/primordia/`](docs/primordia/) 配下に日付入りの craft 文書として落とします。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
