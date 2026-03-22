# swarma

AIエージェントとスウォームのためのグロース実験ループ。

**[swarma.dev](https://swarma.dev)**

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [한국어](README.ko.md) | [Deutsch](README.de.md)

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

あなたのエージェントはタスクを実行する。swarmaはそれをA/Bテストに変える。

仮説と指標を定義する。あとはswarmaがループを回す：実験を実行し、結果をスコアリングし、判定を下し、戦略を更新する。十分なサイクルを経れば、「こうすればうまくいくはず」ではなく「実際にうまくいった」ことが検証済みのプレイブックとして手に入る。

```
strategy.md → 実行 → 計測 → 判定 → 更新された strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

[QMD](https://github.com/glitch-rabin/qmd) と [karpathy autoresearch パターン](https://github.com/karpathy/autoresearch) から得た知見を応用 -- グロースチームが回してきた実験ループを、AIエージェントスウォームに適用したもの。

## なぜこれが存在するのか

Uber、Spotify、Facebook、Airbnb -- あらゆるグロースチームが同じループを回している：仮説を立て、テストし、計測し、学び、繰り返す。勝つチームは頭が良いわけじゃない -- ただ実験の回数が多く、データに素直に従っているだけだ。何千サイクルも回した末に出来上がるプレイブックこそが本当の資産。チームでも、ツールでも、優れたアイデアでもない。蓄積された学びだ。

ボトルネックは常に人間の帯域幅だった。最高のグロースチームでも週2〜5実験が限界。テストを設計し、実行し、結果を待ち、分析し、学びを書き出し、プレイブックを更新する -- それだけの人手が必要になる。ほとんどのチームは時間が足りず、半分のステップを飛ばしている。

10年間こうしたチームを構築・スケールしてきて、パターンは明白だ：ループは機能する。制約はそれを何回回せるか。AIエージェントはその制約を完全に取り除く。人間のチームが2回実験する間に、スウォームは50回実験できる。ただし、実際にループを閉じる何か -- 結果をスコアリングし、判定を下し、戦略を進化させる仕組み -- がなければ意味がない。

それがswarmaの役割だ。大規模グロースチームが当たり前に持っている実験インフラを、どんなエージェントスウォームでも使えるようにパッケージ化したもの。同じループ、同じ厳密さ、同じ複利効果。サイクル数は無制限。50人のチームは不要。

## クイックスタート

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
swarma init                    # インスタンスとスターターチームを作成
swarma cycle starter           # 1サイクル実行して動作を確認
swarma status                  # コスト、実行回数、実験状況
```

Python 3.11+ と [OpenRouter](https://openrouter.ai/) APIキーが必要。GPU不要、PostgreSQL不要、Docker不要。ノートPCでも$5のVPSでも動く。

## ループの仕組み

1. エージェントは毎回実行前に自分の `strategy.md` を読む
2. アウトプットを生成する（コンテンツ、リサーチ、分析 -- チームの業務内容に依る）
3. 安価なLLMがエージェントの指標に基づいてアウトプットをスコアリングする（1〜10、小数点あり）
4. スコアと根拠が `results.tsv` に記録される
5. `min_sample_size` サイクル（デフォルト3〜5）経過後、自動的に判定が下される
6. `strategy.md` が学んだ内容で更新される
7. 次のサイクルは進化した戦略を使う

**スコアリング**: 各アウトプットはルーティングテーブル内の最安モデルによる別のLLMコールで評価される。評価者はアウトプット、現在の戦略、直近5回のスコア、指標定義を参照する。精密なスコア（7ではなく7.3）に加え、根拠と戦略提案を返す。

**判定**: 十分なサンプルが集まると、swarmaは実験平均をベースラインと比較する。20%以上の改善 = **keep**（パターン検証済み、戦略更新）。20%以上の低下 = **discard**（元に戻す）。その中間 = **inconclusive**（記録し、データを増やして再試行）。

数回の実験後、`strategy.md` はこうなる：

```markdown
## Validated (Exp 5)
contrarian opening + specific numbers in first line
> 23% improvement over baseline. keep this pattern.

## Inconclusive (Exp 2)
story-led hooks vs data-led hooks -- no significant difference (avg=8.1 vs baseline=7.9)
> next: increase sample size, results may be noise
```

プレイブックが成長する。チームが賢くなる。あなたは何も触らない。

## チーム = 設定ファイル

チームはフォルダ。コード不要。

```
teams/my-squad/
├── team.yaml          # 目標、フロー、スケジュール、予算
├── program.md         # チームのコンテキストと制約
└── agents/
    ├── researcher.yaml
    └── writer.yaml
```

```yaml
# team.yaml
name: my-squad
goal: find what works.
flow: "researcher -> writer"
schedule: "0 8 * * 1-5"
```

```yaml
# agents/writer.yaml
id: writer
name: Writer
instructions: |
  turn research into a post. max 200 words.
  hook in the first line. practitioner voice.
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 5
  auto_propose: true
```

モデル、ツール、エキスパートレンズは `config.yaml` で設定。エージェントはデフォルトを継承するか、個別にオーバーライドできる。

フローDSLは逐次処理（`a -> b`）、並列処理（`a -> [b, c, d]`）、混合パイプラインに対応。

## 10個のサンプルスクワッド

すぐに使えるスクワッドが [`examples/`](examples/) にある。インスタンスにコピーして実行：

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

| スクワッド | テスト内容 |
|-------|--------------|
| `hook-lab` | 冒頭の一文 -- スクロールを止めるもの |
| `format-wars` | カルーセル vs テキスト vs スレッド vs 画像 |
| `voice-finder` | エンゲージメントがピークになるまでトーンを変える |
| `cta-optimizer` | CTAの配置と表現 |
| `topic-radar` | オーディエンスが実際に関心を持つテーマ |
| `timing-lab` | 投稿時間と頻度の実験 |
| `repurpose-engine` | トップパフォーマーをプラットフォーム間でリサイクルする方法 |
| `thread-lab` | スレッド構成とフックパターン |
| `newsletter-lab` | 件名、送信時間、フォーマット |
| `defi-alpha` | 暗号資産コンテンツにおけるリサーチの深さ vs スピード |

各スクワッドには実際の実験パターンと指標ガイダンスを含む `program.md` が付属。

## インテグレーション

### Hermes Agent

swarmaはMCP serverを公開する。[Hermes](https://github.com/nousresearch/hermes-agent) に接続すれば、エージェントが寝ている間に学習する専用の実験チームが手に入る。

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

Hermesはクリーンなまま -- 方向を示し、計画を承認し、「何を学んだ？」と聞く。泥臭い仕事はswarmaがやる。

### Claude Code / Claude Desktop

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp"]
    }
  }
}
```

### REST API

```bash
swarma serve --port 8282        # 30以上のエンドポイント、OpenAPIドキュメントは /docs
```

### 任意のMCPクライアント

```bash
swarma serve --mcp              # stdio
swarma serve --mcp --mcp-port 8383   # HTTP
```

**注意**: MCPサブプロセスとして実行する場合、MCP設定の `env` ブロックで `OPENROUTER_API_KEY` を渡すこと -- インスタンスの `.env` はサブプロセスに継承されない。

## 知識レイヤー (QMD)

エージェントは `strategy.md` を通じて個別に学習する。チーム間で学びを共有するには、[QMD](https://github.com/glitch-rabin/qmd) を追加する -- 全エージェントのアウトプットをインデックスする検索エンジン。BM25 + ベクトル検索 + リランク。GPU不要。

```bash
pip install qmd
qmd init
qmd serve                          # http://localhost:8181
```

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

全エージェントのアウトプットが自動でインデックスされる。エージェントは他のエージェントが学んだことを検索できる。実験ループが共有メモリを持つようになる。

QMDなしの場合、swarmaはローカルのSQLiteを使用（メタデータのみ）。QMDありの場合、全アウトプット、戦略、結果に対するセマンティック検索が可能になる。

## swarmaが「ではない」もの

- **メモリではない** -- [honcho](https://github.com/plastic-labs/honcho) がメモリを担当する。swarmaは学習ループを担当する。
- **自動化ではない** -- n8n/makeがワークフローを担当する。swarmaは実験を回す。
- **プロンプトライブラリではない** -- [agency-agents](https://github.com/msitarzewski/agency-agents) に135のテンプレートがある。swarmaはそれらに何が有効かを教える。
- **オーケストレーションではない** -- CrewAI/AutoGenがパイプラインを実行する。swarmaはパイプラインを改善するフィードバックループを追加する。

## ロードマップ

- [ ] エキスパート推論レンズ（合成可能な思考フレームワーク）
- [ ] ダッシュボードUI（実験ビューア、プレイブック、戦略の進化）
- [ ] 外部指標の取り込み（Webhook、アナリティクスコールバック）
- [ ] スクワッドマーケットプレイス
- [ ] PyPIで `pip install swarma`

## コントリビューション

swarmaはまだ初期段階。エージェントの実験ループに興味があれば、IssueやPRを歓迎する。

## ライセンス

MIT
