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

Myco は **Agent-First な共生認知基層**——*あなたのエージェントのもう半身*です。記憶レイヤーでも、エージェント・ランタイムでも、スキル・フレームワークでもありません。これは **オートポイエティックな基層（autopoietic substrate）** です：エージェントが知性をもたらし、Myco が記憶・免疫・代謝・自己モデル・そしてそれ自身の進化をもたらす。どちらか片方では完結しません。

> **kernel は安定、substrate は可変。** `pip install` は kernel をリリース版でロックする。エージェントが日々進化させるものすべて（`_canon.yaml`、`notes/`、`docs/primordia/`）は、あなたの substrate の中にあり、12 の MCP verb が駆動する。kernel の進化は upstream のガバナンス: craft → PR → bump。

## クイックスタート

```bash
pip install 'myco[mcp]'          # パッケージ + MCP SDK + コンソールスクリプト
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

2 つのコンソールスクリプトが PATH に載ります：

- `myco` — 12 verb の CLI。
- `mcp-server-myco` — 汎用 MCP stdio ランチャー。どの host にも挿せます。

**Claude Code / Cowork** は公式プラグインで一括導入（hooks + skills + MCP）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**それ以外の MCP host** はこの 1 行設定で統一。Myco は安定したコンソールスクリプトを提供するので、`python` か `python3` か、host がどの venv を spawn するかを気にする必要はありません：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

| Host | 設定パス | 追加方法 |
|---|---|---|
| **Cursor** | `.cursor/mcp.json`（プロジェクト）または `~/.cursor/mcp.json`（グローバル） | 上のスニペットを貼り付け |
| **Windsurf** | `~/.codeium/windsurf/mcp_config.json` | 上のスニペットを貼り付け |
| **Zed** | `~/.config/zed/settings.json` → `context_servers.myco` | `{"source":"custom","command":"mcp-server-myco","args":[]}` |
| **Codex CLI** | ワンライナーまたは `~/.codex/config.toml` | `codex mcp add myco -- mcp-server-myco` |
| **Gemini CLI** | `~/.gemini/settings.json` → `mcpServers.myco` | 上のスニペットを貼り付け |
| **Continue** | `.continue/mcpServers/myco.yaml` | `name: Myco` · `type: stdio` · `command: mcp-server-myco` |
| **Claude Desktop** | `claude_desktop_config.json` → `mcpServers.myco` | 上のスニペットを貼り付け |
| **LangChain / CrewAI / DSPy / Agent Framework** | Python | `StdioServerParameters(command="mcp-server-myco")` |

*Aider は現時点で MCP をネイティブサポートしていません（aider-ai/aider #4506 参照）。コミュニティブリッジ `mcpm-aider` が暫定対応。*

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

3 つの役割——**あなた** が方向を決め、**エージェント** が知性をもたらし、**Myco** が記憶と継続性をもたらす。ハード契約 7 条（R1–R7）はフック・免疫システム・エージェントの規律の三者によって強制されます。全文：[`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## クロスプラットフォーム強制メカニズム

R1–R7 は Claude Code / Cowork では hook が強制。それ以外の host には hook がない — ただし強制は MCP server 自体に組み込まれています:

- **初期化指示。** `initialize` 時に、すべての host に短い R1–R7 サマリーと [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md) へのリンクが届きます。instructions を読む Agent は、最初の tool 呼び出し前に契約を見る。
- **`substrate_pulse` サイドカー。** すべての tool 応答は `substrate_pulse` フィールドを含み、現在の `contract_version`、`substrate_id`、および R1（hunger 未コール）→ R3（sense before assert）へと昇格するルールヒントを運ぶ。サーバサイドからの push であり、Agent が契約を忘れることはできない。

このサイドカーは Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop で host 側設定ゼロで動作します。

## 統合

- **Claude Code / Cowork** —— `/plugin marketplace add Battam1111/Myco` → `/plugin install myco@myco`、または手動で `.claude/` をコピー。どちらでも SessionStart → `hunger`、PreCompact → `session-end` が配線されます。
- **MCP 対応ホスト** —— `mcp-server-myco` コンソールスクリプトを stdio で（または `--transport sse` で HTTP）、もしくは `myco.mcp:build_server` でライブラリ組み込み。
- **下流 substrate** —— `myco propagate` が発行；adapter は `myco.symbionts` に。

## もっと知る

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

コントリビュート：`pip install -e ".[dev]"`；アーキテクチャに関わる変更は [`docs/primordia/`](docs/primordia/) 配下に日付入りの craft 文書として落とします。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
