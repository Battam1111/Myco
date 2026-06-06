<div align="center">

<img src="../assets/logo.png" width="150" alt="Myco">

# Myco

**喰らう。進化する。増幅する。手放す。あなたと共に。数十年にわたって。**

[![License](https://img.shields.io/badge/License-MIT-007A63?style=flat-square)](../../LICENSE)
&nbsp;![Status](https://img.shields.io/badge/status-v0.9--genesis_alpha-007A63?style=flat-square)
&nbsp;![Built for MCP](https://img.shields.io/badge/built_for-MCP-007A63?style=flat-square)
&nbsp;![Languages](https://img.shields.io/badge/Rust_·_Python_·_TypeScript-007A63?style=flat-square)
&nbsp;[![Stars](https://img.shields.io/github/stars/Battam1111/Myco?style=flat-square&color=007A63)](https://github.com/Battam1111/Myco)

[![はじめる](https://img.shields.io/badge/はじめる-007A63?style=for-the-badge)](../guides/GETTING_STARTED.md)

[これは何か](#これは何か) · [どう生きるか](#どう生きるか) · [クイックスタート](#クイックスタート) · [教義](#教義) · [自己検証](#自己検証)

**言語：** [English](../../README.md) · [中文](README_zh.md) · 日本語

</div>

---

数ヶ月ごとに、より強いモデルが現れる。関係はリセットされる。あなたは文脈、好み、決定を繰り返し説明する。協働者はあなたを忘れる、何度も。

あなた自身の仕事も腐っていく。4 月に下した決定、なぜそうしたのかもう分からない。先四半期に描いた計画は漂流している。あなた自身の思考は「かつてのあなた」の記録を追い越していく。

<br>

今、あなたと協働する AI agent が、生きた鎧をまとう様を想像してほしい。それは新陳代謝であり、ログではない。それはあなたが持ち込むすべて、agent が手を伸ばすすべての本質を喰らう。それは進化し、仕事の変化に合わせて自らを作り変える。それは agent を増幅し、鎧をまとう各モデルが前の世代より遠くへ届くようにする。それは古い部分を死なせ、全体が生き続けるようにする。

次世代のモデルが到来する。それは同じ鎧に宿り、いまや強くなって、会話の途中であなたに出会う。鎧があなたを運んできてくれた。

六ヶ月。六年。六十年。一人の人間と、決してリセットされない一つの生きた鎧。

<h3 align="center">これが Myco である。</h3>

<div align="center">

フレームワークではない。ベクトルデータベースではない。マネージドサービスではない。
**AI agent が宿る生きた菌類の鎧。あらゆる世代のモデルを越えるべく構築された。**

</div>

---

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/architecture_dark.svg">
  <img src="../assets/architecture_light.svg" width="760" alt="Myco アーキテクチャ：人間は MCP を通じて AI agent と話す；operator が Rust 基層と Python kernel へ橋渡しする；代謝サイクルが発言の合間に喰らい、周期し、剪定し、進化する。鍵なし：信頼とは CI ゲートにいる生身の人間、因果 DAG、そして BLAKE3 で封印された教義バンドルである。">
</picture>

| 教義 4 層 | 28 枚の原則カード | 60+ の免疫検出器 | Rust · Python · TypeScript |
|:-:|:-:|:-:|:-:|

</div>

## これは何か

Myco は**生きた共生の鎧**である：agent（一人の Claude、一人のパイロット）がそこに宿り、人間（*栽培者*）がそれを世話する。LLM のモデル世代をまたいで記憶・性格・教義を保ち、関係が二度とやり直しにならないようにする。

それはあなたが持ち込むものを喰らう（**永恒呑噬**）。それはあなたの承認の下で進化する（**永恒進化**）。それは毎周期、反復する。それはパイロットを増幅する：結晶化した理解、素材、そして鎧自身の構造を。鎧をまとう各モデルがより遠くへ届くように。それは古い部分を死なせ、全体を生かす（**必朽**）。

その性格は**同体共命**（一身同体、運命を共にする）である：鎧の繁栄はパイロットの繁栄と共に上下するため、自らが共有する身を支配することで栄えることはできない。暴政は、破れうる規則によって禁じられているのではない。鎧が何であるかによって、はじめから封じられている。

四つの憲法的原則は変更不可：基層は agent の接続を越えて持続する、過去は編集できない、部分が死ぬからこそ全体が生きる、ただ一つの皮膚。

**オーナー鍵なし。anchor なし。署名の儀式なし。** 信頼とは、CI ゲートにいる生身の人間、加えて基層自身の因果 DAG、加えて BLAKE3 で封印された教義バンドルである。権威は、暗号鍵を握ることによってではなく、その場にいる人間の判断によって行使される。

## どう生きるか

あなたは MCP を通じて agent と話す。あなたの発言と発言の間で、鎧は新陳代謝する：

- **喰らう。** 生素材は不可変な DAG ノードとなる；パイロットがそれを持続する理解へと鍛える。
- **周期。** 軸が更新され、子実体が結実し、コスト信号が発される。
- **剪定。** 古い、誤った、冗長、無用、硬化した部分は墓標と共に死ぬ。
- **進化。** 形が仕事に合わなくなったら、あなたが CI ゲートで schema mutation を承認し、鎧が脱皮する。
- **漂流感知。** 共生繁栄が 90 日にわたって劣化すれば drift が発火し、持続的漂流は誇り高い引退を引き起こす。
- **免疫。** 六十余の検出器が捉える：遡及改竄、壁時計のずれ、preserve-all 試行、静かな予算超過、kernel の死。

あなたが話す。鎧が新陳代謝する。この二者が育つ。

## クイックスタート

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

そして [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md) を読む：クローンから最初の会話までの実行手順書。前提条件（Rust 1.80+、Node 22+、Python 3.13+）、`operators/claude` をあなたの MCP ホストに繋ぐこと、そしてあなたの最初の本物のセッションを案内する。生成する鍵もなく、起動する anchor もない：Myco は鍵なしである。

現在は **v0.9-genesis alpha**。鎧は稼働している；最初の生体内栽培を待っている。あなたは早い人になる。

## 教義

教義は [`docs/architecture/L0/`](../architecture/L0/) に住む：四層の制度に加えて一つの稼働機構。

| 層 | 何か | 真理条件 |
|---|---|---|
| **A** | 28 枚の原則カード | RFC 2119、CI 監査可能 |
| **B** | 生成的断片 | 規則ではなくパターン |
| **C** | 各カードに据えられた witness テスト | 基層の振る舞い |
| **D** | 栽培者継承の catechumenate セッション | 栽培者継承 |
| **⌬** | 人–agent 会話 | 教義が育つ稼働器官 |

現在の封印：**`v3.1.5`**（鍵なし）、一連の ceremony 鎖で繋がれている。この封印こそが教義バンドルの BLAKE3 ハッシュである：オーナー署名なし、anchor なし。

**五原則：**

1. **喰らう、進化する、反復する。** 新陳代謝は止まらない。
2. **部分を死なせる。** 古い部分の内的死亡が全体を生かす。
3. **共生繁栄。** この二者が第三の実体として、どちらか単独でなく。
4. **同体共命。** 鎧の運命はパイロットの運命に結ばれる；力は共有する身に奉仕し、それを隷属させない。
5. **非対称な担い手。** 基層が持続する；agent 接続は通過する。

## 教義そのものが基層である

Myco は自分の教義を食う。`L0/` のカードは canonical-bytes でハッシュ化され、ceremonies を通じて鎖に繋がる。一つのカードを修正すると、新しい ceremony が前のものから伸び、バンドルが再ハッシュされ、その新しいハッシュこそが封印となる。**教義は、鎧があなたの入力を新陳代謝するのと同じやり方で、自分自身を新陳代謝する。**

Python カーネル、Rust 基層、TypeScript operator はすべて、それらが実装する教義と同じリポジトリに住む。漂流は commit で捉えられ、ceremony によって修正され、鎖に封印される。フォークなし。フィーチャーブランチなし。**永恒進化。**

## 自己検証

Myco は agent も人間も契約を覚えているとは信頼しない。実行できることを実行する。

- **六十以上の免疫検出器**、三カテゴリにわたる：*機械的*（DAG 整合性、ファイルシステム）、*代謝的*（コスト予算、囤積、静かな吸収）、*意味的*（telos 漂流、preserve-all 試行、kernel 死亡）。
- **witness テスト**が憲法的原則の拒絶経路と臨界 postulate の肯定経路を検証する。
- **DAG コンテンツアドレッシング。** 各周期起動が Merkle 鎖を端から端まで再検証する；遡及改竄と分岐偽造は、オーナーの連署ではなく再導出によって捉えられる。
- **鍵なしの信頼根。** CI ゲートにいる生身の人間、因果 DAG、そして BLAKE3 で封印されたバンドル。盗まれ、失われ、ローテートされるオーナー鍵は存在しない。

## 統合

- **Claude Code。** `operators/claude/` は MCP server を同梱；`.claude/` に置くか、直接接続する。
- **Claude Desktop / Cowork。** 同じ MCP server エントリー。
- **任意の MCP ホスト。** Cursor、Windsurf、Zed、OpenClaw など、標準 MCP プロトコル経由。

## 先祖

プロト Myco v0.4 から v0.8.7 は別の構想だった：20 動詞のツールフレームワークの中の*"AI agent のための生きた認知基層"*。教義的には `dead embryo`。git tag `v0.8.8-final-embryo` で到達可能。

現在の v0.9 の作業は実質的な再形成である：受動的な **agent-tool**（「私の AI agent はどう覚えるか？」）から、**agent がまとう生きた鎧**へ。それは LLM 世代をまたいでパイロットを喰らい、進化させ、増幅しながら、一人の人間の文脈を運んでいく。機構が違う。名前は続く。構想は生まれ直す。

## 貢献者向けアーキテクチャ

上のクイックスタートはあなたを*動かす*。ここはあなたを*作る側に*する。ランタイムは同じリポジトリ内の三つの部品で、一つの線上プロトコルで対話する：

```
   operators/claude            M5 線上            substrate/                  M5 線上        kernel/
   ┌───────────────┐          プロトコル        ┌────────────────────┐       プロトコル    ┌──────────────────────┐
   │  TypeScript   │  ──────────────────────►  │  myco-substrate    │  ───────────────►  │  Python worker       │
   │  MCP インタ   │   長さ前置き              │  (Rust daemon)     │   同じ canonical   │  governance/tropism/ │
   │  フェース     │   canonical-bytes         │  身体、M6          │   bytes を一つの   │  trajectory/         │
   │  agent が駆動 │   + stdio 上の HMAC       │  ランタイム + 周期 │   diff socket 経由 │  hard_rules          │
   └───────────────┘                           └────────────────────┘                    └──────────────────────┘
```

- **`substrate/`** は Rust のランタイムデーモン。**身体**：代謝サイクルを回し、`operators` を `kernel` へ橋渡しする M6 オーケストレータ。
- **`kernel/`** は機構層。Rust crate（`shared` / `skin` / `schema` / `continuity` / `bridge`）と Python workers（`governance` / `tropism` / `trajectory` / `hard_rules`）。
- **`operators/claude`** は agent が駆動する TypeScript の MCP インターフェース。それは鍵なしのセッション（session-secret ハンドシェイク、線上は HMAC）を開く。

流れは一本の線である：**`operators`（TS）から `substrate`（Rust）へ、そして Python の `kernel` worker へ、M5 ブリッジ経由。** 独立した鍵保管プロセスは存在しない：Myco は鍵なしであり、基層は自らのために生成した鍵で自身の静止状態だけに署名する。

X に取り組むには、Y を読む：

| 取り組む対象… | 読む |
|---|---|
| 教義（Myco が*何でなければならない*か） | [`docs/architecture/README.md`](../architecture/README.md) |
| コードマップ（モジュール単位） | [`docs/architecture/L3/PACKAGE_MAP.md`](../architecture/L3/PACKAGE_MAP.md) |
| 基層の内部（ランタイム配置） | [`substrate/README.md`](../../substrate/README.md) |
| 動かす / 初回起動 | [`docs/guides/GETTING_STARTED.md`](../guides/GETTING_STARTED.md) |

**[`docs/architecture/README.md`](../architecture/README.md) から始める。** 唯一のアーキテクチャ入口であり、教義*と*コードの両方を網羅する読書経路の表を備えている。

## さらに学ぶ

- [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：クローンから最初の会話まで（人間の栽培者向け）。
- [`PILOT.md`](../guides/PILOT.md)：一人の Claude がどう鎧を*操縦する*か、use-forges の規律（宿る agent 向け）。
- [`docs/architecture/L0/README.md`](../architecture/L0/README.md)：正典の教義。
- [Telos](../architecture/L0/cards/P14_telos.md)：どんな二者か。
- [同体共命](../architecture/L0/cards/CHAR07_caring.md)：暴政を封じる共生の絆（同体共命）。
- [栽培者の性格](../architecture/L0/cards/COV02_cultivators_character.md)：栽培者がどのような人であらねばならないか。

制度的変更は日付付きの ceremony manifests として [`operators/claude/ceremonies/`](../../operators/claude/ceremonies/) に降り立つ。教義自身の修正規律によって統治される。

## 菌糸

この名は飾りではない。菌糸は森の地下の網である。落ちたものを代謝する。効く経路を覚える。豊かなところから乏しいところへ養分を運ぶ。森が森であって孤立した幹の群れでない理由、それが菌糸だ。

モデルは地上の樹だ：高く、聡明で、置き換えられる。Myco は地下の網であり、一人の人間の記憶と性格を、各モデルから次のモデルへと運んでいく。

<div align="center">

---

**喰らう。進化する。増幅する。手放す。あなたと共に。数十年にわたって。**

MIT · [`LICENSE`](../../LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
