<div align="center">

<img src="assets/logo_dark_280.png" alt="Myco" width="200">

# Myco

**AI エージェントのための自律認知基質。**

*あなたのエージェントは CPU。Myco はそれ以外のすべて ―― そして OS は自分でアップグレードする。*

[![PyPI](https://img.shields.io/badge/PyPI-v0.2.0-blue?style=for-the-badge)](https://pypi.org/project/myco/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Lint](https://img.shields.io/badge/Lint-23%2F23%20全緑-brightgreen?style=for-the-badge)](#アーキテクチャ)

[クイックスタート](#クイックスタート) · [何ができるか](#何ができるか) · [なぜ違うのか](#なぜ違うのか) · [アーキテクチャ](#アーキテクチャ) · [参加する](#参加する) · [ライセンス](#ライセンス)

**言語：** [English](README.md) · [中文](README_zh.md) · 日本語（現在）

</div>

---

2024年、LangChain を使った。

2025年、LangGraph のほうがいいと言われた。

次は CrewAI。そして DSPy。Hermes。AutoGen。毎月「今度こそ決定版」が現れる。前のやつを覚えている人はもういない。ツールは増える。あなたの生産性は増えない。

---

50 のリポジトリをフォローした。読んだのは 3 つ。

200 の記事を保存した。読んだのは 10。

Hacker News を開くたびに「後で読む」リストが伸びる。後では来ない。情報はどんどん降ってくるが、あなたの頭には何も残らない。

---

3 週間前に書いた API メモ。バージョンが変わった。

先月のベストプラクティス。コミュニティはもう覆した。

誰もチェックしていない。あなた自身も。知識は書いた瞬間から腐り始めているのに、腐ったことに気づく仕組みがどこにもない。

---

**そして、怠け者が勝った。**

何もしなかった。メモも整理しなかった。ツールも比較しなかった。ただ毎日エージェントと話した。それだけ。

6 ヶ月後、そいつの AI がチームで一番賢い。

なぜか。エージェントが覚えていたからだ。話すたびに知識が蓄積され、圧縮され、古くなったものは勝手に捨てられ、残ったものだけが次の会話に引き継がれた。本人は何もしていない。基質がやった。

---

<div align="center">

### これが Myco だ。

</div>

> **Myco は AI エージェントのための自律認知基質（Autonomous Cognitive Substrate）。** エージェントは CPU ―― 生の計算力だけで、記憶はゼロ。Myco はそれ以外のすべてを担う：メモリ、ファイルシステム、OS、周辺機器。そしてこの OS は自分自身をアップグレードする。進化はすべて非パラメトリック ―― ディスク上のテキスト、構造、lint ルール。モデルの重みには一切触れない。だからベンダーに依存せず、モデルを入れ替えても生き残り、LLM が最も得意とする媒体の中で価値を蓄積し続ける。

---

## クイックスタート

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco && pip install -e ".[mcp]"
myco init --auto-detect my-project
```

3行のコマンド。環境を自動検出 — Claude Code · Cursor · VS Code · Codex · Cline · Continue · Zed · Windsurf · Cowork — 検出したもの全部を一発で設定。

編集可能インストール — エンジン自体を含むシステム全体を書き換えられる。いじりたくなければそのままでいい。勝手に進化する。

---

## 何ができるか

- **食べる** ―― コード、決定、摩擦、学び。会話の中で生まれた知識を、ゼロ摩擦で捕捉する。迷ったら食え。
- **消化する** ―― 生ノートを七段パイプライン（Discover → Evaluate → Extract → Integrate → Compress → Verify → Excrete）で代謝。出口のない消化管は腫瘍だ。
- **圧縮する** ―― ストレージは無限、注意力は有限。エージェントのコンテキストに収まる形に、荷重構造だけを残して圧縮する。
- **排出する** ―― 腐った知識、置き換えられた事実、二度と読まれないノート。Myco は自分で検出し、自分で捨てる。溜め込むだけのシステムは腫瘍になる。
- **進化する** ―― lint ルール、圧縮戦略、canon スキーマ。基質は自分自身のルールを書き換える。エージェントの振る舞いではなく、エージェントが立つ地面を進化させる。
- **免疫する** ―― 23 次元の lint が矛盾、孤立参照、知識ドリフト、構造的劣化を検出する。Markdown リンターには見えない、ファイル横断の意味的一貫性を守る。

---

## なぜ違うのか

| | メモリサービス | 知識コンパイラ | 知識有機体 |
|---|---|---|---|
| **代表例** | Mem0, Zep, LangMem | Karpathy LLM Wiki | **Myco** |
| **中核の動詞** | 保存する | コンパイルする | **代謝する** |
| **ライフサイクル** | なし。入って、座って、クエリされる | 取り込みと lint だけ | raw → digesting → extracted → integrated → excreted |
| **自己検証** | なし | 矛盾/孤立の基本チェック | 23 次元免疫系（L0--L22） |
| **自己進化** | なし | 静的スキーマ | Craft プロトコルが基質のルール自体を進化 |
| **排出** | しない。溜まる一方 | しない | 死知識検出・自動剪定・時間期限排出 |

**メモリサービスは保存する。コンパイラはコンパイルする。Myco は代謝する。**

取り込むだけで排出しないシステムは、生きた知識ベースではない ―― 腫瘍だ。知識に完全なライフサイクルを与えるシステムは Myco だけだ：誕生、消化、検証、圧縮、そして ―― 居場所を稼がなくなったら ―― 排出。生物学の語彙は装飾ではない。アーキテクチャそのものだ。

---

## アーキテクチャ

```
                   ┌─────────────────────────────────────┐
                   │          LLM エージェント            │
                   │     （CPU ―― 生の計算、RAM なし）    │
                   └──────────────▲──────────────────────┘
                                  │ 21 MCP ツール + CLI
                                  │ (eat / digest / lint / hunger …)
                   ┌──────────────┴──────────────────────┐
                   │         Myco カーネル（OS）          │
                   │  代謝 · 自己モデル · lint ·          │
                   │  進化エンジン · メタボリック入口      │
                   │      ↑ upstream 吸収                 │
                   │      ↓ カーネル更新                  │
                   └──────────────┬──────────────────────┘
                                  │
      ┌───────────────────────────┼────────────────────────────┐
      ▼                           ▼                            ▼
 ┌─────────┐                ┌─────────┐                  ┌─────────┐
 │ プロジェ │               │ プロジェ │                  │ プロジェ │
 │ クト A   │               │ クト B   │                  │ クト C   │
 └─────────┘                └─────────┘                  └─────────┘
    （インスタンス ―― wiki / _canon / notes / log）
```

**カーネル**はプロジェクト非依存の認知 OS。**インスタンス**はプロジェクトディレクトリ ―― OS 上で走るアプリケーションだ。カーネルの改善は下流へ伝播し、インスタンスで発見された摩擦は upstream outbox を通じてカーネルに還流する。これはメタファではなく、Myco の物理構造そのものだ。

すべての進化は**非パラメトリック**：ディスク上のテキスト、構造、lint ルール。モデルの重みには一切触れない。だからベンダーをまたいで動き、モデルを入れ替えても生き残り、LLM が最も得意とする媒体の中で価値を蓄積し続ける。

---

## 生物学語彙の早見表

Myco の動詞は代謝のメタファだ。理論を読まなくても、この表があれば始められる。

| Myco 動詞 | 意味 | CLI | MCP ツール |
|---|---|---|---|
| `eat` | コンテンツを持続ノートとして捕捉 | `myco eat` | `myco_eat` |
| `digest` | ノートをライフサイクルに沿って推進（raw → extracted → integrated → excreted） | `myco digest` | `myco_digest` |
| `evaluate` | 生ノートが基質に値するかを評価 | `myco evaluate` | （CLI のみ） |
| `extract` | 消化中ノートから荷重構造を抽出 | `myco extract` | （CLI のみ） |
| `integrate` | 抽出済みノートを既存の知識体に接続 | `myco integrate` | （CLI のみ） |
| `compress` | N 個のノートを 1 個に合成（監査証跡付き） | `myco compress` | `myco_compress` |
| `uncompress` | 圧縮を元に戻し、入力ノートを復元 | `myco uncompress` | `myco_uncompress` |
| `prune` | 死知識を走査して自動排出 | `myco prune` | `myco_prune` |
| `view` | フィルタ付きでノートを閲覧（閲覧数を追跡） | `myco view` | `myco_view` |
| `lint` | 23 次元の基質健全性チェック | `myco lint` | `myco_lint` |
| `correct` | 直前の lint が提案した自動修復を適用 | `myco correct` | （CLI のみ） |
| `forage` | 外部資料の管理（追加/一覧/消化） | `myco forage` | `myco_forage` |
| `inlet` | 来歴追跡付きの外部コンテンツ取り込み | `myco inlet` | `myco_inlet` |
| `hunger` | 代謝ダッシュボード（バックログ・古いノート・死知識） | `myco hunger` | `myco_hunger` |
| `absorb` | 下流インスタンスからカーネル改善を同期 | `myco upstream absorb` | `myco_upstream` |
| `graph` | リンクグラフ分析（バックリンク・孤立・クラスタ・統計） | `myco graph` | `myco_graph` |
| `cohort` | タグ共起分析・圧縮提案・ギャップ検出 | `myco cohort` | `myco_cohort` |
| `session` | エージェント会話の索引・検索・剪定 | `myco session` | `myco_session` |

全コマンド一覧は `myco --help` または [English README](README.md) を参照。

---

## 参加する

[CONTRIBUTING.md](CONTRIBUTING.md) を参照。特にインパクトが大きい貢献：

1. **戦場レポート** ―― [Open Problems](docs/open_problems.md) のどれかに対する実戦フィードバック。
2. **プラットフォームアダプタ** ―― あなたが使っているエージェント環境向けの適配を [`docs/adapters/`](docs/adapters/) に。
3. **メタボリック入口の設計スケッチ** ―― discover / evaluate / extract フェーズ。
4. **翻訳** ―― [English](README.md) · [中文](README_zh.md) · 日本語（本ファイル）。

## ライセンス

MIT ―― [LICENSE](LICENSE) を参照。

---

<div align="center">

**あなたのエージェントは CPU。Myco はそれ以外のすべて ―― そして OS は自分でアップグレードする。**

</div>
