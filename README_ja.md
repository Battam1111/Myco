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
  <a href="#myco-とは">Myco とは</a> · <a href="#どう生きているか">どう生きているか</a> · <a href="#クイックスタート">クイックスタート</a> · <a href="#十八の-verb">verb 一覧</a> · <a href="#自己検証">自己検証</a>
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

Myco はあなたの AI エージェントの生きた認知基層です。

エージェントが読み書きするすべて — コード、論文、決定、摩擦 — が、あなたのファイルシステム上に markdown + YAML として住み、菌糸グラフに織り込まれます。エージェントは原料を喰らい、それを統合知識へ消化し、免疫でドリフトを検出し、プロジェクト間に学びを広げ、そして仕事が古い形を超えたときには基層そのものを作り直します。**これらすべてを動かす kernel 自身もまた substrate です** — デフォルトで editable、それを使うエージェント自身の手で保守されます。

フレームワークではありません。ベクター DB でもありません。マネージドサービスでもありません。あなたが話しかけるエージェントのために生きている、ファイルシステムです。

これが今できるのは、アイデアが新しいからではなく、エージェントがようやくこのシステムを自分で維持できる賢さに達したからです。過去の試みは、人間が追いつけずに死にました。Myco は「維持するのはエージェント」という前提を、すべての表面、すべての verb、すべてのルールに織り込んでいます。

## どう生きているか

あなたが話します。エージェントが聞きます。あなたの発話と発話の間に、Myco は代謝を回します：

- **摂取（Ingestion）。** `hunger` が何が足りないかを尋ね、`eat` があなたが指したものを何でも取り込み（パス、URL、一段落）、`sense` と `forage` はすでにある素材を走査します。
- **消化（Digestion）。** `assimilate` が raw ノートを統合知識へ煮込み、`sporulate` が統合知識を散布可能な提案へ濃縮します。
- **循環（Circulation）。** `traverse` が菌糸グラフを辿り吻合健全性を確認し、`propagate` が学びを下流 substrate へ発行します。
- **恒常性（Homeostasis）。** `immune` が 7 条のハードルールに対して 25 次元 lint を走らせ、`senesce` が各セッションを優雅に終えます。
- **進化（Evolution）。** 基層の形が合わなくなったとき — canon フィールドが足りない、新しい lint 次元が必要、verb の変更 — `fruit` が 3 ラウンドの craft 提案を書き、`winnow` が形を篩い、`molt` が contract バンプを出荷します。

18 の verb、1 つの manifest、2 つの面（観察のための CLI、エージェントが駆動する MCP サーバー）。あなたは何も覚えず、エージェントが駆動します。

## 五つの原則

- **エージェント専用。** すべての表面はエージェントのための一次資料であり、人間の読者向けドキュメントではありません。
- **万物を吞噬。** 取り込みにフィルタなし。信号を取り逃がす代償は、取り込みすぎる代償より常に高い。
- **自己進化する形。** canon、lint 次元、verb、契約そのもの — すべて統治された craft ループを通じて可変です。
- **「最終版」は存在しない。** `integrated` は状態であって終点ではない。今日の結論は明日の raw 素材。
- **菌糸ネットワーク。** すべてのノードは辿ることで他のすべてに繋がります。孤児は死んだ組織。

## kernel 自体が substrate

Myco のソースツリーそのものが substrate です。ルートに `_canon.yaml`、エージェント入口ページとしての `MYCO.md`、そして `docs/primordia/` に、すべての contract バンプの根拠となる 3 ラウンド craft 文書。`src/myco/` の Python コードは、その生態系の最も内側の環 — 誰かが書いた読み取り専用の成果物ではありません。

だから通常のインストールはソースを clone して `pip install -e` するものです。Myco を使うエージェントは、Myco を保守するエージェントと同じ存在。新しい lint 次元が必要なら、自分で `myco ramify` で骨組みを作り、`myco fruit` で提案を書き、`myco molt` で出荷します。fork も不要、PR を待つ必要もありません。**永恒進化。**

PyPI は bootstrap チャネルおよびライブラリ消費者向けパスとして残りますが、通常のインストール経路ではありません。

## クイックスタート

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

リポジトリを `~/myco` に clone し、`pip install -e` を走らせ、書き込み可能な kernel を残します。その後、任意のプロジェクトで substrate を germinate：

```bash
cd your-project
myco germinate . --substrate-id your-project
```

Myco をエージェントホストに 1 コマンドで組み込む：

- **Claude Code** — `/plugin marketplace add Battam1111/Myco`、続いて `/plugin install myco@myco`。
- **Claude Desktop / Cowork** — 2 ステップ: (1) `myco-install host cowork` で MCP エントリを書き込み; (2) [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) から `myco-<ver>.plugin` をダウンロードし、Claude Desktop の Settings → Plugins → Upload にドラッグ。Claude Desktop がアカウント専用 Cowork marketplace にアップロードし、以降の全セッションで `myco-substrate` スキルが自動インストールされます。Cowork は hooks もローカル plugin dir も参照しないため、ドラッグ＆ドロップが唯一の永続パスです。
- **その他の MCP host** — `myco-install host <cursor | windsurf | zed | vscode | openclaw | claude-desktop | gemini-cli | codex-cli | goose>`、または `--all-hosts` で本機の全ホストを自動検出。
- **公式 MCP Registry 経由** — 名前空間自動解決に対応するクライアント向けに、[`io.github.Battam1111/myco`](https://registry.modelcontextprotocol.io/v0/servers?search=Battam1111) として登録済み。

スキーマが異なる 9 つの host 向けスニペット、Python フレームワーク adapter（LangChain / CrewAI / DSPy / Smolagents / Agno / PraisonAI / MS Agent Framework / Claude Agent SDK）、ライブラリ組み込み例は [`INSTALL.md`](docs/INSTALL.md) に収録。

## 十八の verb

6 つのサブシステム。すべての verb は菌類生物学の術語であり、語の意味が verb の挙動と一致しています。

- **Germination** — `germinate` が新しい substrate を発芽させる。
- **Ingestion** — `hunger`（何が足りない？）、`eat`（raw を取り込む）、`sense`（キーワード検索）、`forage`（取り込み可能パスを走査）。
- **Digestion** — `assimilate`（raw → integrated）、`digest`（単一ノート昇格）、`sporulate`（integrated → 散布可能な提案）。
- **Circulation** — `traverse`（グラフを辿る）、`propagate`（下流へ発行）。
- **Homeostasis** — `immune`（25 次元 lint、`--fix` で機械的な修復）。
- **Cycle** — `senesce`（セッション休眠）、`fruit`（3 ラウンド craft）、`winnow`（craft のゲート）、`molt`（contract バンプの出荷）、`ramify`（新 dim / verb / adapter を scaffold）、`graft`（substrate ローカルプラグイン管理）、`brief`（人間向け状態ロールアップ）。

すべての verb は [`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml) に住みます。CLI（`myco VERB`）も MCP tool 表面も、機械的にこの manifest から派生します — 2 つの面にとっての 1 つの真理の源。下流 substrate は Myco を fork せずに、`.myco/plugins/` に自前の dimensions や verb を `ramify` できます。

## 自己検証

Myco はエージェントが契約を覚えていると信用しません。強制します。

- **25 次元 lint**、4 カテゴリに分かれる — *mechanical*（canon 不変式、write-surface、LLM 境界）、*shipped*（package ↔ canon バージョン整合）、*metabolic*（raw 堆積、古い integrated ノート）、*semantic*（グラフ連結性、孤児検出）。`myco immune --fix` が機械的に直せるものは直します。
- **7 条のハードルール（R1–R7）** がすべてのセッションを支配 — boot ritual、session-end、sense-before-assert、eat-on-friction、cross-reference-on-creation、write-surface discipline、top-down layering。完全契約は [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md) に。
- **Pulse サイドカー。** MCP tool 応答のすべてに `substrate_pulse` が乗ります。現在の contract バージョンと、セッション進行に合わせて昇格していくルールヒント（R1 → R3 → …）を運びます。サーバ側からの push — エージェントは忘れようがありません。
- **Write-surface 強制。** `_canon.yaml::system.write_surface.allowed` の外への書き込みはすべて `WriteSurfaceViolation` で拒否されます。規律はメカニズムであって、お願いではありません。

host 側の設定はゼロ。R1–R7 は MCP サーバー自身に組み込まれているので、どのクライアント — Claude Code、Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands — も boot 時に同じ契約を受け取ります。

## 統合

- **Claude Code。** 公式プラグインで MCP + hooks + slash skills を一括導入。あるいは手動で `.claude/` をコピー。
- **Cowork（Claude Desktop local-agent-mode）。** 2 ステップ: (1) `myco-install host cowork` で MCP を書き込み; (2) [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) から `.plugin` をダウンロードし、Claude Desktop のプラグインアップロードへドラッグ。Claude Desktop がアカウント専用 Cowork marketplace にアップロードし、以降のセッションで `myco-substrate` スキルが自動装着され、エージェントが `_canon.yaml` を見た瞬間に R1-R7 へ従います。Cowork は hooks もローカル plugin dir も参照しないため、ドラッグ＆ドロップが唯一の永続パスです — 詳細は [`INSTALL.md`](docs/INSTALL.md) を参照。
- **任意の MCP ホスト。** 10 つは `myco-install` で自動化済み。残り 9 つは [`INSTALL.md`](docs/INSTALL.md) に per-host スニペットあり。その他のクライアントは `mcp-server-myco` stdio で直接。
- **Python エージェントフレームワーク。** LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、MS Agent Framework、Claude Agent SDK — すべて `StdioServerParameters(command="mcp-server-myco")` で Myco を消費。
- **下流 substrate。** `myco propagate` が発行し、adapter は `myco.symbionts` に住みます。

## もっと知る

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

アーキテクチャに関わる変更は、[`docs/primordia/`](docs/primordia/) 配下に日付入りの craft 文書として落とされます。リリースは毎回、3 ラウンドの討論を経て `molt`、そして自動化ワークフローが PyPI + MCP Registry + GitHub release に扇状展開します。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
