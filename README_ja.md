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

LangChain。LangGraph。CrewAI。DSPy。Claude Code skills。OpenHands。OpenClaw。数ヶ月ごとに次のフレームワークが降りてきて、あなたはまた移行する。

ノートも腐る。三週間前に読んだ API は変わっている。去年書いたドキュメントはもう間違っている。あなたの AI は先週の決定すら覚えていない。新しい会話のたびに、毎回ゼロから始まる。

<br>

一つの生きた基層を想像してください。それはフレームワーク、論文、API、コードリポジトリ、データセット、決定、摩擦を吞噬します。エージェントが本当に読めるグラフにそれらを繋いでおきます。自身のドリフトを自分で見つけて直します。仕事があなたの古い形を超えたら、自分で形を変えます。半年。六年。移行なし。

<h3 align="center">これが Myco です。</h3>

---

## Myco とは

Myco はあなたの AI エージェントの生きた認知基層です。**フレームワークではありません。フレームワークを吞噬する基層です。**

Myco はコードリポジトリ、フレームワークドキュメント、データセット、論文、チャットログ、決定、摩擦を吞噬します。エージェントが指を差せるものすべてが原料になります。それを消化し、菌糸グラフに繋ぎ、免疫でドリフトを検出し、プロジェクト間で知識を propagate します。仕事の形が変わったら、Myco も一緒に変わります。エージェントが craft で提案、あなたが承認、kernel が bump。新しい canon フィールド、新しい lint 次元、新しい verb、新しい subsystem。中身が完全に書き直されても、それは `myco` のバージョンアップであって、新しい依存ではありません。基層そのものは二度と捨てられません。

**あなたは二度と移行しません。**

これが今できるのは、アイデアが新しいからではありません。エージェントがようやく、このシステムを自分で維持できる賢さに達したからです。過去の試みは、人間が追いつけずに死にました。Myco は「維持するのはエージェント」という前提を、すべての表面、すべての verb に織り込んでいます。

### 五つの原則

- **エージェント専用。** あなたは Myco を閲覧しません。あなたはエージェントと話し、エージェントが Myco を読みます。すべての表面（`_canon.yaml`、notes、doctrine、boot brief）はエージェントが読むための一次資料であり、人が読むドキュメントではありません。
- **万物を吞噬。** 取り込みにフィルタなし。コードリポジトリ、フレームワーク、論文、データセット、ログ、半熟の思いつき、raw の決定。エージェントが指せるものを、基層はすべて食べます。形は後で整えます。信号を取り逃がす代償は、取り込みすぎる代償より常に高い。
- **自己進化する形。** canon schema、lint 次元、verb、契約そのもの、すべて可変です。仕事が現在の形を超えたら、エージェントが提案し、あなたが承認し、Myco が形を変えます。凍った基層は死んだ基層です。
- **「最終版」は存在しない。** `integrated` は状態であって終点ではない。今日消化したノートは、明日 context が鋭くなれば再消化できる。省察は鼓動です。
- **菌糸ネットワーク。** すべての note、canon フィールド、doctrine ページは互いに辿れるようにリンクされます。孤児は死んだ組織。このグラフこそエージェントが知識を読む方法なので、常に生かしておく必要があります。

### 三つの役割

**あなた** が方向を決めます。CLI を覚えない、ファイルを整理しない、次のセッションで自分のプロジェクトを説明し直さない。

**エージェント** が知性をもたらします。あなたの言葉を読み、Myco を読み、verb を選び、書き戻す。

**Myco** が代謝を回します。あなたの発話の合間に、何が足りないかを聞き（`hunger`）、raw を取り込み（`eat`）、raw を構造化知識に煮る（`reflect`、`digest`、`distill`）、ドリフトに対してアイデンティティを守り（`immune`）、学びをプロジェクト間に広げる（`propagate`）。12 個の verb、1 つの manifest、2 つの面：観察のための CLI、エージェントが駆動する MCP サーバー。

> **デフォルトで editable install。kernel 自体が substrate。** Myco のソースツリーそのものが substrate です（`_canon.yaml`、`MYCO.md`、`docs/primordia/` を持っています）。`src/myco/` の kernel コードは、その substrate の最も内側の環に過ぎません。この環を読み取り専用の `site-packages` に閉じ込めることは、永恒进化 + 永恒迭代と矛盾します — エージェントが、他人が書いたコードの消費者になってしまい、自分が保守するコードの著者ではなくなります。だから主たるインストール経路はソースを clone して `pip install -e` すること。PyPI は bootstrap チャネルとライブラリ消費者用の経路として残りますが、通常のインストール経路ではありません。

## クイックスタート

1 行、事前の `git clone` 不要、bootstrap 残留もなし：

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

このリポジトリを `~/myco` に clone して `pip install -e` を走らせ、書き込み可能な kernel + substrate を残します。あるいは 2 ステップ形式も可：

```bash
pip install 'myco[mcp]'
myco-install fresh ~/myco         # clone + editable install；--dry-run でプレビュー
```

その後、任意のプロジェクトで下流 substrate を bootstrap：

```bash
cd /path/to/your/project
myco genesis . --substrate-id my-project
```

kernel のアップグレードは、`~/myco` の中で `git pull` するだけで、`pip install --upgrade` は使いません：

```bash
cd ~/myco && git pull && myco immune        # アップグレード後、ドリフトがないか免疫で検証
```

3 つのコンソールスクリプトが PATH に載ります：

- `myco`：12 verb の CLI。
- `mcp-server-myco`：汎用 MCP stdio ランチャー。どの host にも挿せます。
- `myco-install`：主要 7 つの MCP host に 1 コマンドで導入。

**Claude Code と Cowork** は公式プラグインで一括導入（MCP サーバー、hooks、slash skills を一度に配線）：

```
/plugin marketplace add Battam1111/Myco
/plugin install myco@myco
```

**その他の MCP host** も 1 コマンドで済みます：

```bash
myco-install cursor        # または: claude-desktop, windsurf, zed, vscode, openclaw
```

あるいは汎用スニペットを host の設定ファイルに貼り付け。`mcpServers` ファミリー（Claude Desktop、Cursor、Windsurf、Cline、Roo Code、Gemini CLI、Qwen Code、JetBrains AI、Augment Code、AiderDesk）で動作します：

```json
{ "mcpServers": { "myco": { "command": "mcp-server-myco", "args": [] } } }
```

設定スキーマが異なる 9 つの host（VS Code Copilot `servers`、Zed `context_servers`、OpenClaw `mcp.servers` + CLI、OpenHands TOML、OpenCode / Kilo Code `mcp`、Codex CLI TOML、Goose YAML `extensions`、Continue YAML ブロック、Warp `mcp_servers`）はそれぞれ正確なスニペットを [`docs/INSTALL.md`](docs/INSTALL.md) に収録。同じ INSTALL.md は Python フレームワーク adapter（LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、Microsoft Agent Framework、Claude Agent SDK）もカバーします。

ライブラリ組み込み：

```python
from myco.mcp import build_server
build_server().run()                   # stdio（デフォルト）
build_server().run(transport="sse")    # HTTP SSE
```

### 非進化インストール（ライブラリ消費者、CI、vendor）

Myco を別の Python プロジェクトの依存として import する場合、あるいは kernel を意図的に凍結したコンテナで動かす場合、従来の読み取り専用インストールはそのまま使えます：

```bash
pip install 'myco[mcp]'
```

ただし `myco scaffold`、Myco 自身の kernel レベル `craft`/`bump`、あらゆる形の kernel 進化はこのパス上では遮断されます — これは設計であり、バグではありません。読み取り専用インストールは消費者向けであり、著者向けではありません。

### Myco に貢献する場合

主たるインストール経路と同じ — `myco-install fresh` がコントリビューター向けパスです。`--extras dev,mcp` でテストツールも同時に引けます：

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco --extras dev,mcp
cd ~/myco
pytest
```

## 日常のフロー

エージェントが駆動します。あなたは何も覚えません。12 個の verb は 5 つのサブシステムに分類されます：

| サブシステム | Verbs | 何が起こるか |
|---|---|---|
| **Genesis** | `genesis` | 新しい substrate をブートストラップ。 |
| **Ingestion** | `hunger`、`sense`、`forage`、`eat` | 今何が必要か；キーワード検索；取り込み可能なファイルの列挙；raw note を記録。 |
| **Digestion** | `reflect`、`digest`、`distill` | raw を integrated に昇格；integrated を doctrine に蒸留。 |
| **Circulation** | `perfuse`、`propagate` | 参照グラフの健全性；下流 substrate への発行。 |
| **Homeostasis** | `immune` | 4 カテゴリ / 8 次元の一貫性 lint、`--fix` 対応。 |
| *（meta）* | `session-end` | `reflect` と `immune --fix`、PreCompact により自動発火。 |

CLI の使い方は `myco VERB` で、グローバル flag（`--project-dir`、`--json`、`--exit-on`）は verb の **前** に置きます。MCP は 1 verb につき 1 tool、パラメータは `src/myco/surface/manifest.yaml`（CLI と MCP 共通の SSoT）から機械的に派生します。

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

ハード契約 7 条（R1 から R7）はフック、免疫システム、エージェントの規律の三者によって強制されます。全文は [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md)。

## クロスプラットフォーム強制メカニズム：どのホストも置き去りにしない

R1 から R7 は Claude Code と Cowork では hook が強制します。それ以外の host（Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands）では、強制は **MCP server 自体** に組み込まれています：

- **初期化指示。** `initialize` 時に、すべての host に短い R1 から R7 サマリーと [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md) へのリンクが届きます。instructions を読む Agent は、最初の tool 呼び出し前に契約を見ます。
- **`substrate_pulse` サイドカー。** すべての tool 応答は `substrate_pulse` フィールドを含み、現在の `contract_version`、`substrate_id`、および R1（hunger 未コール）から R3（sense before assert）へ昇格するルールヒントを運びます。サーバサイドからの push であり、Agent が契約を忘れることはできません。

host 側設定ゼロ、すべての MCP クライアントで動作します。

## 統合

- **Claude Code と Cowork**：`/plugin marketplace add Battam1111/Myco`、続いて `/plugin install myco@myco`。または手動で `.claude/` をコピー。
- **任意の MCP ホスト**：7 つの主要ホストは `myco-install <client>`、それ以外は `mcp-server-myco` stdio。正確な per-host スニペットは [`docs/INSTALL.md`](docs/INSTALL.md)。
- **Python エージェントフレームワーク**：LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、Microsoft Agent Framework、Claude Agent SDK はすべて `StdioServerParameters(command="mcp-server-myco")` で Myco を消費。
- **下流 substrate**：`myco propagate` が発行、adapter は `myco.symbionts` に。

## もっと知る

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

コントリビュート：`pip install -e ".[dev]"`；アーキテクチャに関わる変更は [`docs/primordia/`](docs/primordia/) 配下に日付入りの craft 文書として落とします。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
