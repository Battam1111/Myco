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
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco"><img src="https://glama.ai/mcp/servers/Battam1111/Myco/badges/score.svg" alt="Glama score"></a>
</p>

<p align="center">
  <a href="https://glama.ai/mcp/servers/Battam1111/Myco">
    <img src="https://img.shields.io/badge/Glama%20%E3%81%A7-%E4%BB%8A%E3%81%99%E3%81%90%E8%A9%A6%E3%81%99-8b5cf6?style=for-the-badge" alt="Glama で今すぐ試す" height="36">
  </a>
</p>

<p align="center">
  <sub>Claude&nbsp;Code：<code>/plugin install myco@myco</code> &nbsp;·&nbsp; Claude&nbsp;Desktop：<code>myco-install host cowork</code> &nbsp;·&nbsp; 任意の&nbsp;MCP&nbsp;host：<code>pip install 'myco[mcp]'</code></sub>
</p>

<p align="center">
  <a href="#myco-とは">Myco とは</a> · <a href="#どう生きているか">どう生きているか</a> · <a href="#クイックスタート">クイックスタート</a> · <a href="#十九の-verb">verb 一覧</a> · <a href="#自己検証">自己検証</a>
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

エージェントが読み書きするすべて、コードの一行一行、論文の一本一本、決定の一つ一つ、摩擦の一つ一つが、あなたのファイルシステム上に素の markdown + YAML として住みます。ファイル同士はファイル名で相互参照し、エージェントが本当に読むグラフを織ります。エージェントは原料を喰らい、統合知識へ消化し、自分の仕事を免疫で検査してドリフトを防ぎ、学びをあなたの全プロジェクトへ広げ、基層の形が仕事の形に合わなくなったときには、基層そのものを作り直します。**これらすべてを動かす kernel 自身もまた substrate です**。デフォルトで editable、それを使うエージェント自身の手で保守されます。

フレームワークではありません。ベクターデータベースでもありません。マネージドサービスでもありません。あなたが話しかけるエージェントのために生きている、ファイルシステムです。

アイデアは実装より古い。変わったのはエージェントの方です。今日のモデルは、ようやく自分の道具を自分で生かし続けられる賢さに達しました。自己維持型の知識システムへの過去の試みはすべて、同じ地点で死にました。ループの中の人間が追いつけなくなったのです。Myco はそのループをエージェントの中に移しました。すべての表面、すべての verb、すべてのルールが「維持するのはエージェント」を前提にしているので、ループの中の人間はもう荷重構造ではありません。

## どう生きているか

あなたが話します。エージェントが聞きます。あなたの発話と発話の間に、Myco は代謝を回します。

- **摂取（Ingestion）。** `hunger` が何が足りないかを尋ねます。`eat` はあなたが指したものを何でも取り込みます。パス、URL、一段落、何でも。`sense` と `forage` はすでに手元にある素材を走査します。`excrete` は、誤って捕獲した raw ノート（タイプミス、取り違え、重複）を、サイレント削除ではなく監査用の墓石へ安全に移します。
- **消化（Digestion）。** `assimilate` は raw ノートを統合知識へ一括で煮込みます。`digest` は単一ノートを昇格させます。`sporulate` は統合知識を散布可能な提案へ濃縮します。
- **循環（Circulation）。** `traverse` はグラフを辿り、その連結性を報告します。`propagate` は学びを下流 substrate へ発行します。
- **恒常性（Homeostasis）。** `immune` は 7 条のハードルールに対して 25 次元の lint を走らせます。`senesce` は各セッションを綺麗に閉じます。
- **進化（Evolution）。** 基層の形が仕事の形に合わなくなったとき（canon フィールドが足りない、新しい lint 次元が必要、verb を変えたい）、`fruit` が 3 ラウンドの craft 提案を書き、`winnow` が形を篩い、`molt` が contract バンプを出荷します。

19 の verb、1 つの manifest、2 つの面。あなたが観察するための CLI、エージェントが駆動するための MCP サーバー。あなたは何も覚える必要がありません。駆動するのはエージェントです。

## 五つの原則

- **エージェント専用。** すべての表面、すべてのメッセージ、すべての verb の形は、エージェントのための一次資料です。人間の読者向けのドキュメントではありません。
- **万物を吞噬。** 取り込みにフィルタはありません。信号を取り逃がす代償は、取り込みすぎる代償より常に高い。
- **自己進化する形。** canon、lint 次元、verb、契約そのもの。すべて可変で、すべて同じ統治された craft ループを通じて書き換わります。
- **「最終版」は存在しない。** `integrated` は状態であって終点ではありません。今日の結論は、明日の raw 素材です。
- **菌糸ネットワーク。** すべてのノードは辿ることで他のすべてのノードに繋がります。孤児は死んだ組織です。

## kernel 自体が substrate

Myco のソースツリーそのものが substrate です。ルートに `_canon.yaml`。エージェント入口ページとしての `MYCO.md`。`docs/primordia/` には、すべての contract バンプの根拠となる 3 ラウンド craft 文書。`src/myco/` の Python コードは、その生態系の最も内側の環です。誰かが書いた読み取り専用の成果物ではありません。

だから通常のインストールはソースを clone して `pip install -e` を走らせます。Myco を使うエージェントは、Myco を保守するエージェントと同じ存在です。新しい lint 次元が必要なら、自分で `myco ramify` で骨組みを作り、`myco fruit` で提案を書き、`myco winnow` で形を篩い、`myco molt` で出荷します。fork は不要。PR を待つ必要もありません。長命の feature branch も不要です。**永恒進化。**

PyPI は bootstrap チャネルおよびライブラリ埋め込み用として残りますが、通常のインストール経路ではありません。

## クイックスタート

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

このコマンドはリポジトリを `~/myco` に clone し、そこで `pip install -e` を走らせ、書き込み可能な kernel を残します。その後、任意のプロジェクトで substrate を germinate します。

```bash
cd your-project
myco germinate . --substrate-id your-project
```

Myco をエージェントホストに 1 コマンドで組み込みます。

- **Claude Code。** `/plugin marketplace add Battam1111/Myco` を実行し、続いて `/plugin install myco@myco`。
- **Claude Desktop / Cowork。** 2 ステップ。(1) `myco-install host cowork` で MCP エントリを書き込み、(2) [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) から `myco-<ver>.plugin` をダウンロードして、Claude Desktop の Settings → Plugins → Upload へドラッグ。Claude Desktop はそれをアカウント専用の Cowork marketplace にアップロードし、以降のすべてのセッションで `myco-substrate` スキルが自動インストールされます。
- **その他の MCP host。** `myco-install host <cursor | windsurf | zed | vscode | openclaw | claude-desktop | gemini-cli | codex-cli | goose>`、もしくは `--all-hosts` を渡すと本機の全ホストを自動検出します。
- **公式 MCP Registry 経由。** 名前空間を自動解決するクライアント向けに、名前空間 [`io.github.Battam1111/myco`](https://registry.modelcontextprotocol.io/v0/servers?search=Battam1111) が登録済みです。

スキーマが異なる 9 つの host 向けスニペット、Python フレームワーク adapter（LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、MS Agent Framework、Claude Agent SDK）、ライブラリ組み込み例は、すべて [`INSTALL.md`](docs/INSTALL.md) に収録されています。

## 十九の verb

6 つのサブシステム。すべての verb は菌類生物学の術語であり、語の意味が verb の挙動と一致しています。

- **Germination。** `germinate` が新しい substrate を発芽させる。
- **Ingestion。** `hunger`（何が足りない？）、`eat`（raw を取り込む）、`sense`（キーワード検索）、`forage`（取り込み可能パスを走査）、`excrete`（監査用墓石付きで raw ノートを安全に削除）。
- **Digestion。** `assimilate`（raw から integrated へ、一括）、`digest`（単一ノートの昇格）、`sporulate`（integrated から散布可能な提案へ）。
- **Circulation。** `traverse`（グラフを辿る）、`propagate`（下流 substrate へ発行）。
- **Homeostasis。** `immune`（25 次元 lint、`--fix` で機械的に直せるものは直す）。
- **Cycle。** `senesce`（セッション休眠）、`fruit`（3 ラウンドの craft）、`winnow`（craft の形を篩う）、`molt`（contract バンプの出荷）、`ramify`（新しい次元、verb、adapter を scaffold）、`graft`（substrate ローカルプラグイン管理）、`brief`（人間向け状態ロールアップ）。

すべての verb は [`src/myco/surface/manifest.yaml`](src/myco/surface/manifest.yaml) に住みます。CLI（`myco VERB`）も MCP tool 表面も、この manifest から機械的に派生します。2 つの面にとって、1 つの真理の源。下流 substrate は、Myco を fork することなく、自前の dimensions や verb を `.myco/plugins/` に `ramify` できます。

## 自己検証

Myco はエージェントが契約を覚えていると信用しません。強制します。

- **25 次元の lint**、4 カテゴリに分かれます。*mechanical*（canon 不変式、write-surface、LLM 境界）、*shipped*（package と canon のバージョン整合）、*metabolic*（raw の堆積、古い integrated ノート）、*semantic*（グラフ連結性、孤児検出）。`myco immune --fix` が機械的に直せるものは直します。
- **7 条のハードルール（R1 から R7）** がすべてのセッションを支配します。boot ritual、session-end、sense-before-assert、eat-on-friction、cross-reference-on-creation、write-surface discipline、top-down layering。完全契約は [`L1_CONTRACT/protocol.md`](docs/architecture/L1_CONTRACT/protocol.md) に。
- **Pulse サイドカー。** MCP tool 応答のすべてに `substrate_pulse` が乗ります。現在の contract バージョンと、セッションの進行に合わせて昇格していくルールヒント（R1、続いて R3、そして先へ）を運びます。サーバ側からの push。エージェントは忘れようがありません。
- **Write-surface 強制。** `_canon.yaml::system.write_surface.allowed` の外への書き込みは、すべて `WriteSurfaceViolation` で拒否されます。規律はメカニズムであって、お願いではありません。

host 側の設定はゼロ。R1 から R7 は MCP サーバー自身に組み込まれているので、どのクライアント（Claude Code、Cursor、Windsurf、Zed、Codex、Gemini、Continue、Claude Desktop、OpenClaw、OpenHands）も boot 時に同じ契約を受け取ります。

## 統合

- **Claude Code。** 公式プラグインで MCP、hooks、slash skills を一括導入。あるいは手動で `.claude/` をコピー。
- **Cowork（Claude Desktop local-agent-mode）。** 2 ステップ。(1) `myco-install host cowork` で MCP を書き込み、(2) [GitHub releases](https://github.com/Battam1111/Myco/releases/latest) から `.plugin` をダウンロードして、Claude Desktop のプラグインアップロードへドラッグ。Claude Desktop はそれをアカウント専用の Cowork marketplace にアップロードし、以降のセッションで `myco-substrate` スキルが自動装着され、エージェントが `_canon.yaml` を見た瞬間に R1 から R7 へ従います。Cowork は hooks もローカル plugin dir も参照しないため、ドラッグ＆ドロップが唯一の永続パスです。詳細は [`INSTALL.md`](docs/INSTALL.md) を参照。
- **任意の MCP ホスト。** 10 つは `myco-install` で自動化済み。残り 9 つは [`INSTALL.md`](docs/INSTALL.md) に per-host スニペットあり。その他のクライアントは `mcp-server-myco` stdio で直接起動できます。
- **Python エージェントフレームワーク。** LangChain、CrewAI、DSPy、Smolagents、Agno、PraisonAI、MS Agent Framework、Claude Agent SDK。すべて `StdioServerParameters(command="mcp-server-myco")` で Myco を消費します。
- **下流 substrate。** `myco propagate` が発行します。adapter は `myco.symbionts` に住みます。

## もっと知る

[`L0_VISION.md`](docs/architecture/L0_VISION.md) · [`L1_CONTRACT/`](docs/architecture/L1_CONTRACT/) · [`L2_DOCTRINE/`](docs/architecture/L2_DOCTRINE/) · [`INSTALL.md`](docs/INSTALL.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [Issues](https://github.com/Battam1111/Myco/issues)

アーキテクチャに関わる変更は、[`docs/primordia/`](docs/primordia/) 配下に日付入りの craft 文書として落ちます。リリースは毎回、3 ラウンドの討論を経て `molt`、そして自動化ワークフローが PyPI、MCP Registry、GitHub release へ扇状展開します。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam1111/Myco/releases)
