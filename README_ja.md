<p align="center">
  <a href="https://github.com/Battam1111/Myco">
    <img src="https://raw.githubusercontent.com/Battam1111/Myco/main/assets/logo_light_512.png" width="160" alt="Myco">
  </a>
</p>

<h1 align="center">Myco</h1>

<p align="center"><b>すべてを喰らう。永遠に進化する。あなたはただ話すだけ。</b></p>

<p align="center">
  <a href="https://pypi.org/project/myco/"><img src="https://img.shields.io/pypi/v/myco?style=flat" alt="PyPI"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat" alt="License"></a>
  <a href="https://github.com/Battam1111/Myco"><img src="https://img.shields.io/github/stars/Battam1111/Myco?style=flat" alt="Stars"></a>
</p>

<p align="center">
  <a href="#はじめに">はじめに</a> · <a href="#日常の流れ">日常</a> · <a href="#何ができるか">機能</a> · <a href="#なぜ違うのか">差別化</a> · <a href="#アーキテクチャ">構造</a> · <a href="#エコシステム">エコシステム</a>
</p>

<p align="center">
  <b>Languages:</b> <a href="README.md">English</a> · <a href="README_zh.md">中文</a> · 日本語
</p>

---

2024年、LangChain を使った。2025年、LangGraph のほうがいいと言われた。次は CrewAI。そして DSPy。Hermes。毎月誰かが「これこそ最高のフレームワークだ」と言う。ツールを選ぶのに費やした時間のほうが、どのツールで何かを成し遂げた時間より長い。

フレームワークだけじゃない。論文、ブログ、ベストプラクティス、新モデル、新API、新パラダイム、毎日更新される。50のリポジトリをフォローして、読んだのは3つ。200の記事をブックマークして、読んだのは10。ノートアプリには500件のメモがある。最後に整理したのは3ヶ月前。

努力が足りないんじゃない。**この世界はもう、誰も追いつけない速さで動いている。**

もっと痛いのは、苦労して整理したメモ、あの経験、あの「前はどうやったっけ」、腐りかけている。3週間前に書いたAPIの呼び方、バージョンが変わった。先月まとめたベストプラクティス、コミュニティはもうひっくり返した。知識ベースはどんどん大きくなるのに、そのうちどれだけがまだ正しいか？ 誰も知らない。**何もチェックしてくれるものがない。**

メモは「これはもう古いよ」と教えてくれない。ブックマークは重複を自動でまとめてくれない。AIは先週あなたが何を決めたか覚えていない。新しい会話を開くたびに、すべてゼロからやり直し。

<br>

別の生き方を想像してみろ。

メモを整理しない。フレームワークを比較しない。論文を追わない。AIにプロジェクトの背景を繰り返し説明しない。バカみたいにただ人間の言葉で話す。

でも6ヶ月後、あなたのAIは誰のよりも賢い。すべてのプロジェクトの完全な履歴を知っている。あなたの分野の最新の論文やツールを自動で喰らった。知識の盲点を自分で見つけて埋めた。古い知識がまだ正しいか自分でチェックした、間違っていたものは、もう捨てた。自分の作業ルールさえ書き換えた。古いルールでは足りなかったから。

<h3 align="center">これが Myco だ。</h3>

---

## Myco とは何か、何でないか

Myco は **Agent-First 共生認知基質**（Agent-First symbiotic cognitive substrate）——*あなたのエージェントのもう半身*だ。

**記憶レイヤー**（Mem0/Zep）**ではない**。**エージェントランタイム**（Hermes/LangGraph）**でもない**。**スキルフレームワーク**（PUA/nuwa）**でもない**。外付けの**インフラでもない**。

これは**自己創出する基質**だ：エージェントが知性をもたらし、Myco が記憶・免疫・代謝・自己モデル・自己進化をもたらす——どちらが欠けても完全ではない。CPU と、それが宿る「記憶-免疫-代謝-自己モデル」器官との関係に近い。四つの語——*Agent-First / Symbiotic / Cognitive / Substrate*——はそれぞれ重量を担っており、どれか一つでも落とせばカテゴリーは「ただの記憶ツール」というデフォルトに崩れ落ちる。

---

## はじめに

**デフォルトは編集可能インストール。** Myco は自分で変異する——skill が自分を書き換え、ルールが進化し、エンジン自体が substrate だ。PyPI からピン止めインストール = 一つのスナップショットに自分を凍結させること。編集可能インストール = 変異のすべてがあなたの作業ツリーにゼロコストで届く。これが Myco の全部の意味だ。どちらでも**設定ゼロ**——Myco は新しいプロジェクトに初めて入った時に **substrate を自動で芽吹かせる**。`myco seed` を覚える必要はない。

**ステップ 1——clone してエンジンを編集可能インストール：**

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
```

コマンド一つ、全ホスト共通。エンジンコードはあなたの clone の中にあり、その場で変異する。`git pull` だけで上流の変異が届く、再インストール不要。

**ステップ 2——あなたの agent に繋ぐ。**

**Cowork / Claude Code**——plugin バンドルは repo に同梱：

```bash
# clone 後：
# - Cowork：plugin/myco-v0.3.3.plugin をドラッグ＆ドロップ
# - Claude Code：`/plugin install plugin/myco-v0.3.3.plugin`
```

どんなプロジェクトを開いても、`SessionStart` hook が `myco hunger --execute` を発火させ、初回起動時にプロジェクトディレクトリへ最小の substrate を静かに芽吹かせる。その後は `eat` / `digest` / `reflect` / `immune` のすべての代謝動詞が即座に動く。

**その他の MCP を話す agent**——Cursor / Continue / Zed / Codex / Cline / Windsurf / VS Code / …：

```bash
myco seed --auto-detect my-project                  # 検出したホスト全部を一発で設定
```

`myco seed` はあなたのマシン上の対応ホストをすべてスキャンし、それぞれの設定ファイルを書き出す。今は 9 ホスト対応、エコシステムの拡大に合わせて増える。

**ピン止めリリースを使いたい？** `pip install 'myco>=0.3.3'` でも動く。ただし「作業ツリー内でのその場変異」という特性は失う。Myco を活きた substrate じゃなく安定した依存として使いたい時だけこの道を選べ。

**逃げ道**。`MYCO_NO_AUTOSEED=1` で初回接触時の自動芽吹きを無効化。`MYCO_PROJECT_DIR=/path/to/shared/substrate` でプロジェクトごとの substrate をやめて、グローバルで一つの substrate を共有できる。

## 日常の流れ

インストールした後は、大抵あなたは Myco の存在を意識しない——agent が MCP ツール経由で勝手に駆動する。でも、知っておく価値のある 6 つの動詞がある：

| あなたが言う / 打つ | それが何をするか |
|---|---|
| `myco hunger` | 健康ダッシュボード：raw ノート、陳腐化した知識、消化待ち、シグナル。`--execute` で自動修復。 |
| `myco eat <内容>` | 決定、洞察、摩擦点、あるいは外部素材を raw ノートとして取り込む。 |
| `myco digest <id>` | 成熟した raw ノートを長期知識（wiki / MYCO.md / コード）に昇格。 |
| `myco search <クエリ>` | substrate 全体に意味 + 構造検索をかける。 |
| `myco reflect` | 会話の学びを沈殿させる。コンテキスト圧縮時に自動で走る。 |
| `myco immune --fix` | 29 次元の一貫性 lint + 機械的な自動修復。セッション終了時に自動で走る。 |

6 つすべてが MCP ツールでもある（`myco_hunger`、`myco_eat`、……）ので、agent が直接呼べる。合計 25 ツール、完全なリストは [`docs/agent_protocol.md`](docs/agent_protocol.md)。

## 何ができるか

- 🧬 **すべてを喰らう**。論文、コード、ブログ、会話、何でも食わせろ。ファイルとして保存するんじゃない、能力に消化する。
- 🛡️ **自己診断する**。29 次元の免疫 lint がセッション終了ごとに走る。古くなった事実、壊れた相互参照、矛盾——機械的に検出、機械的に修復。
- 💀 **死ぬべきものは死ぬ**。長く触られず、読まれず、終端ステータスのノートは自動で排泄される。排泄のない知識システムは腫瘍だ。
- 🔄 **永遠に進化する**。コンテンツだけじゃない、エンジン自体のルール、スキル、作業手順も変異する。システム全体が生きている。
- 🍄 **すべてが繋がる**。すべてのファイルが菌糸ネットワークのノード。孤児ノートは自動でリンクされる。知識は孤立した記録じゃない、どんどん密になる網だ。
- 🤖 **あなたはただ話すだけ**。25 の MCP ツール、13 の運用原則、完全自動。人間は技術的な詳細を一切知らなくていい。

## なぜ違うのか

|  | 保存して終わり | コンパイルして終わり | **Myco** |
|---|---|---|---|
| 入れた後 | 置いてある | 少し整理する | **消化 → 検証 → 圧縮 → 接続 → 排泄** |
| 知識が古くなったら | 誰も気にしない | 誰も気にしない | **免疫 lint が検出、自動修復が走る** |
| 知識が増えたら | どんどん膨れる | どんどん膨れる | **どんどん精錬される——原子が長期真理に圧縮される** |
| 新しいツールが出たら | 手動で切り替え | 手動で移行 | **新ツールの精髄を自動で喰らう** |
| 新しいプロジェクトを開いたら | 白紙 | 白紙 | **自動芽吹き。セッション開始時には substrate がもう生きている。** |
| 時間が経つほど | 散らかる | 古くなる | **賢くなる** |

## アーキテクチャ

```
あなた（人間の言葉で話す）
  │
  ▼
AI Agent（思考・実行）          ←───────┐
  │   MCP で自動接続                    │
  ▼                                   │
Myco substrate                        │
  ├── notes/             知識原子、ライフサイクルあり（raw → digesting → extracted → integrated → excreted）
  ├── wiki/              原子から精錬された長期知識
  ├── _canon.yaml        すべての数字・名前・パスの唯一の真実
  ├── skills/            自己進化する操作手順
  ├── src/myco/          エンジンコード（編集可能・変異可能——そう、コード自体も進化する）
  └── 免疫システム       29 次元の一貫性 lint、セッション終了で自動修復
  │                                   │
  └─────────── 代謝ループ ─────────────┘
               (eat → digest → reflect → immune → prune)
```

3 つの役割：**あなた**が方向を、**agent** が知性を、**Myco** が記憶と進化を。どれが欠けても成り立たない。

代謝ループは絶え間なく回る。`SessionStart` → `hunger --execute` が注意すべきものを浮かび上がらせる。あなたの下した決定は即座に `eat` される。成熟した raw ノートは wiki エントリへ `digest` される。`PreCompact` → `reflect` + `immune --fix` がコンテキスト圧縮前に沈殿させる。死んだ知識は `prune` される。無限に繰り返す。

## エコシステム

**9 つの agent が `myco seed --auto-detect` で自動検出される**：

| Cowork | Claude Code | Cursor | VS Code | Codex | Cline | Continue | Zed | Windsurf |
|---|---|---|---|---|---|---|---|---|

**Plugin バンドル**（Cowork + Claude Code）：一つの `myco-v0.3.3.plugin` ファイルに MCP サーバー、8 スキル（`myco:boot` / `:eat` / `:digest` / `:hunger` / `:reflect` / `:search` / `:observe` / `:absorb`）、2 つの hook（`SessionStart`、`PreCompact`、ハード契約を強制する）が入っている。ファイルは repo の `plugin/myco-v0.3.3.plugin` に同梱——一度 clone すれば、Cowork か Claude Code にインストールするだけ。

**MCP サーバー**：`python -m myco.mcp_server`——25 ツール全部を露出する stdio サーバー。標準 MCP 準拠、どの host でも動く。

**ハード契約**（自動で強制される）：
1. すべてのセッションは `myco_hunger(execute=true)` で始まる——SessionStart hook。
2. すべてのセッションは `myco_reflect` + `myco_immune(fix=true)` で終わる——PreCompact hook。
3. プロジェクトについて何か事実を主張する前に、まず `myco_sense` を呼ぶ。
4. 決定・洞察・摩擦点はすべて、会話の最後にまとめるんじゃなく、その場で `myco_eat` される。
5. 新しいファイルを作ったら、関連ファイルへの相互参照を追加する（孤児 = 死んだ知識）。
6. `_canon.yaml::system.write_surface.allowed` に挙げられたパスにだけ書き込む。

ルール 1-2 は機械的に強制。ルール 3-6 は agent の規律で、免疫 lint の L26-L28 次元が浮かび上がらせる。

## トラブルシューティング

**`ModuleNotFoundError: No module named 'myco'`**——plugin の MCP / hook が走る Python 環境にエンジンが入っていない。その環境で Myco clone から `pip install -e ".[mcp]"` を実行（またはピン止めなら `pip install 'myco>=0.3.3'`）。

**agent が「Myco のソースがマウントされていない」と言う**——agent の推論バグ。Myco は PyPI パッケージで、ソースツリーをマウントする必要はない。agent をプロジェクトルートの `_canon.yaml`（`$CLAUDE_PROJECT_DIR` 配下）に向けろ。

**`SessionStart` hook がタイムアウトする**——非常に大きな substrate（1 万+ ノート、密な菌糸グラフ）はデフォルトの 60s を超えることがある。`.claude/settings.local.json` で `timeout` を上げるか、`myco hunger --fast` を使え。

**空のディレクトリで自動芽吹きが拒否される**——意図通り。Myco はプロジェクトマーカー（`.git`、`pyproject.toml`、`package.json`、`README.md`、……）が一つもないディレクトリでは芽吹きを拒否する。home / システムディレクトリの汚染を防ぐため。マーカーを一つ作るか、明示的に `myco seed --level 1` を走らせろ。

## 参加する

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp,dev]"
pytest tests/              # すべての動詞と次元の単体テスト
myco immune --project-dir . # Myco 自身の免疫システムで自分を lint
```

Issue、PR、新しい host adapter はいつでも歓迎。Kernel 層の変更の提案・レビュー手順は [`CONTRIBUTING.md`](CONTRIBUTING.md)、[agent プロトコル](docs/agent_protocol.md)、[craft プロトコル](docs/craft_protocol.md) を参照。

MIT · [`LICENSE`](LICENSE) · [PyPI](https://pypi.org/project/myco/) · [Releases](https://github.com/Battam11