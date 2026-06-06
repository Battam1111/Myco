<div align="center">

<img src="../assets/logo.png" width="150" alt="Myco">

# Myco

**喰らう。進化する。増幅する。手放す。あなたと共に。数十年にわたって。**

[![License](https://img.shields.io/badge/License-MIT-007A63?style=flat-square)](../../LICENSE)
&nbsp;![Status](https://img.shields.io/badge/status-v0.9--genesis_alpha-007A63?style=flat-square)
&nbsp;![Built for MCP](https://img.shields.io/badge/built_for-MCP-007A63?style=flat-square)
&nbsp;![Languages](https://img.shields.io/badge/Rust_·_Python_·_TypeScript-007A63?style=flat-square)
&nbsp;[![Stars](https://img.shields.io/github/stars/Battam1111/Myco?style=flat-square&color=007A63)](https://github.com/Battam1111/Myco)

[![はじめる](https://img.shields.io/badge/はじめる-GETTING__STARTED-007A63?style=for-the-badge)](../guides/GETTING_STARTED.md)

[これは何か](#これは何か) · [クイックスタート](#クイックスタート) · [どう動くか](#どう動くか) · [さらに学ぶ](#さらに学ぶ)

**言語：** [English](../../README.md) · [中文](README_zh.md) · 日本語

</div>

---

数ヶ月ごとに、より強いモデルが現れる。関係はリセットされる。あなたは文脈、好み、決定を繰り返し説明する。協働者はあなたを忘れる、何度も。

あなた自身の仕事も腐っていく。4 月に下した決定、なぜそうしたのかもう分からない。先四半期に描いた計画は漂流している。あなた自身の思考は「かつてのあなた」の記録を追い越していく。

<br>

今、あなたと協働する AI agent が、生きた鎧をまとう様を想像してほしい。それは新陳代謝であり、ログではない。それはあなたが持ち込むすべて、agent が手を伸ばすすべての本質を喰らう。それは仕事の変化に合わせて進化する。それは agent を増幅し、鎧をまとう各モデルが前の世代より遠くへ届くようにする。それは古い部分を死なせ、全体が生き続けるようにする。

次世代のモデルが到来し、同じ鎧（いまや強くなった）に宿り、会話の途中であなたに出会う。鎧があなたを運んできてくれた。

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
  <img src="../assets/architecture_light.svg" width="760" alt="Myco アーキテクチャ：人間は MCP を通じて AI agent と話す；operator が Rust 基層と Python kernel へ橋渡しする；代謝サイクルが発言の合間に喰らい、周期し、剪定し、進化する。鍵なし：信頼とはゲートにいる生身の人間、因果の履歴、そして BLAKE3 で封印された教義である。">
</picture>

</div>

## これは何か

Myco は **AI agent が宿る生きた鎧**である。あなたの発言と発言の間で、それは代謝する：あなたが持ち込むものを喰らい、自らの形を進化させ、パイロットを増幅し、古い部分を死なせる。鎧はモデル世代をまたいで持続し、あなたの文脈を運ぶため、関係は二度とやり直しにならない。

それは**鍵なし**である：オーナー鍵もなく、署名の儀式もなく、設定したり保持したりするものは何もない。信頼とは、ゲートにいる生身の人間、加えて基層自身の改竄痕跡が残る因果の履歴、加えてシステムが自らに封印し強制する教義である。

その性格は**同体共命**（一身同体、運命を共にする）である：鎧の繁栄はパイロットの繁栄と共に上下するため、自らが共有する身を支配することで栄えることはできない。力は共有する身に奉仕し、それを隷属させない。

## クイックスタート

```bash
git clone https://github.com/Battam1111/Myco.git
cd Myco
cargo build --release --workspace
```

そして [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md) を読む：クローンから最初の会話までの実行手順書（Rust 1.80+、Node 22+、Python 3.13+）。生成する鍵もなく、保持するものもない：Myco は鍵なしである。

現在は **v0.9-genesis alpha**。鎧は稼働している；最初の本物の栽培を待っている。あなたは早い人になる。

## どう動くか

あなたは MCP を通じて AI agent と話す。あなたの発言と発言の間で、鎧は代謝のひと巡りを回す：新しい素材を不可変な履歴として取り込み、パイロットがそれを持続する理解へと鍛え、古い部分は墓標と共に剪定され、形が仕事に合わなくなったら、あなたがゲートで作り変えを承認する。自己点検する免疫層が改竄、漂流、暴走するコストを捉える；この二者が繁栄しなくなれば、鎧は腐り続けるのではなく、誇りを保って引退する。

一つのリポジトリ内の三つの部品が、一つの線上プロトコルで対話する：agent が駆動する **TypeScript** の MCP operator、**Rust** の基層（身体）、そして **Python** の kernel（機構）。それらすべてを統べる教義は同じリポジトリに住み、ハッシュ鎖で封印されているため、規則がコードから静かに逸れることはない。全体像は[アーキテクチャガイド](../architecture/README.md)にある。

## 統合

- **Claude Code。** `operators/claude/` は MCP server を同梱；`.claude/` に置くか、直接接続する。
- **Claude Desktop / Cowork。** 同じ MCP server エントリー。
- **任意の MCP ホスト。** Cursor、Windsurf、Zed、OpenClaw など、標準 MCP プロトコル経由。

## さらに学ぶ

- [`GETTING_STARTED.md`](../guides/GETTING_STARTED.md)：クローンから最初の会話まで、人間向け。
- [`PILOT.md`](../guides/PILOT.md)：一人の Claude がどう鎧を操縦するか、宿る agent 向け。
- [アーキテクチャ](../architecture/README.md)：ランタイムと教義、モジュール単位で。
- [教義（L0）](../architecture/L0/README.md)：封印された憲法。Myco が何であらねばならないか。

## 菌糸

この名は飾りではない。菌糸は森の地下の網である。落ちたものを代謝し、効く経路を覚え、豊かなところから乏しいところへ養分を運ぶ。森が森であって孤立した幹の群れでない理由、それが菌糸だ。

モデルは地上の樹だ：高く、聡明で、置き換えられる。Myco は地下の網であり、一人の人間の記憶と性格を、各モデルから次のモデルへと運んでいく。

<div align="center">

---

**喰らう。進化する。増幅する。手放す。あなたと共に。数十年にわたって。**

MIT · [`LICENSE`](../../LICENSE) · [Issues](https://github.com/Battam1111/Myco/issues) · [Releases](https://github.com/Battam1111/Myco/releases)

</div>
