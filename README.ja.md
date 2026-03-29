# swarma

グロースループを自動化する。

**[swarma.dev](https://swarma.dev)**

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md)

---

![Version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![PyPI](https://img.shields.io/pypi/v/swarma)

あなたのエージェントはタスクを実行する。swarmaはそれをグロース実験に変える。

改善したいことを記述するだけ。swarmaがチームを生成し、実際のグロース知識をシードとして与え、実験を実行し、結果をスコアリングし、判定を下し、戦略を進化させる。十分なサイクルを経ると、実際に効果のあるものだけで構成された検証済みのplaybookが出来上がる。

1フォルダ = 1チーム。1サイクル = 1実験。playbookは自動的に書き上がる。

## GROWSループ

すべてのサイクルはGROWSに従う。5つのステップ、例外なし:

```
  Generate       Run         Observe       Weigh        Stack
  仮説生成 --> 実験実行 --> シグナル観測 --> 判定 --> playbook蓄積
     ^                                                  |
     └──────────────────────────────────────────────────┘
```

| ステップ | 内容 |
|------|-------------|
| **G -- Generate** | エージェントが自身の`strategy.md`を読み、仮説を提案する。「逆張りの導入文は、データ主導のフックよりも保存数で上回る。」 |
| **R -- Run** | エージェントが仮説を有効にした状態で実行する。リサーチ、コピー、分析など、チームが行う作業のアウトプットを生成する。 |
| **O -- Observe** | 別のLLMがエージェントのターゲット指標に対してアウトプットをスコアリングする(1-10スケール、小数点必須)。スコアと根拠が`results.tsv`に記録される。 |
| **W -- Weigh** | `min_sample_size`サイクル(デフォルト3-5)後、swarmaが実験平均とベースラインを比較する。20%以上の向上 = **keep**。20%以上の低下 = **discard**。その中間 = **inconclusive**。 |
| **S -- Stack** | 検証されたパターンは`strategy.md`に書き戻され、共有playbookにプッシュされる。次のサイクルでは進化した戦略から新しい仮説を生成する。 |

これはUber、Spotify、Airbnbのすべてのグロースチームが実行しているのと同じループだ。勝つチームはより賢いわけではない。より多くの実験を実行し、データに耳を傾けている。swarmaは人間の帯域幅のボトルネックを取り除く。人間のチームが2つの実験を行う間に、スウォームは50の実験を実行する。

## クイックスタート

```bash
pip install swarma
```

ソースからインストール:

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma && pip install -e .
```

```bash
swarma init                                        # インスタンスとスターターチームを作成
swarma cycle starter --topic "why do startups fail?"   # 1サイクル実行
swarma status                                      # コスト、実行回数、実験状況
```

Python 3.11+と[openrouter](https://openrouter.ai/) APIキーが必要。GPU不要、PostgreSQL不要、Docker不要。ノートPCや$5のVPSで動作する。

## ゴールからチームを生成する

エージェントを手動で設定する必要はない。やりたいことを記述すれば、swarmaがチームを構築する。

```bash
swarma team create my-growth --from-goal "improve landing page conversion rate"
```

これはLLMを呼び出し、適切なエージェント、フロー、モデル、そして最初の実験仮説を備えたチームを設計する。生成されたチームには以下が含まれる:

- `team.yaml` -- ゴール、フロー、予算
- `agents/*.yaml` -- 具体的な指示を持つ個別エージェント設定
- `program.md` -- 実験パターンと制約
- すぐに実行可能な最初の実験

ビジネスコンテキストを追加するとより良い結果が得られる:

```bash
swarma team create growth-lab \
  --from-goal "optimize our signup funnel" \
  --context "B2B SaaS, 500 free users, 2% conversion to paid" \
  --budget 50
```

## ループの仕組み(詳細)

GROWSループの実際の動作:

1. エージェントは毎回の実行前に`strategy.md`を読む
2. アウトプットを生成する(リサーチ、コピー、分析など、チームが行う作業)
3. 安価なLLMがエージェントの指標に対してアウトプットをスコアリングする(1-10スケール、小数点必須)
4. スコアと根拠が`results.tsv`に記録される
5. `min_sample_size`サイクル(デフォルト3-5)後、判定が自動的に下される
6. `strategy.md`が学習内容で更新される
7. 次のサイクルでは進化した戦略を使用する

**スコアリング**: 各アウトプットは、ルーティングテーブル内の最も安価なモデルを使用した別のLLMコールで評価される。評価者はアウトプット、現在の戦略、直近5回のスコア、指標の定義を確認する。精密なスコア(7ではなく7.3)と根拠、戦略提案を返す。

**判定**: 十分なサンプルが集まった後、swarmaが実験平均とベースラインを比較する。20%以上の改善 = **keep**(パターン検証済み、戦略更新)。20%以上の低下 = **discard**(元に戻す)。その中間 = **inconclusive**(記録し、より多くのデータで再試行)。

数回の実験を経ると、`strategy.md`はシード知識から検証済みパターンへと進化する:

```markdown
## Validated (Exp 5)
逆張りの導入 + 最初の行に具体的な数字
> ベースラインに対して23%改善。このパターンを維持する。

## Inconclusive (Exp 2)
ストーリー主導のフック vs データ主導のフック -- 有意な差なし (avg=8.1 vs baseline=7.9)
> 次回: サンプルサイズを増やす、結果はノイズの可能性あり
```

## 実際のメトリクスをフィードバックする

LLMの自己評価は初期の代理指標にすぎない。本番環境では、実世界のシグナルをフィードバックする:

```bash
# 単一メトリクスを記録
swarma metric log hook-lab copywriter 4.2 --metric ctr_pct

# 特定の実験に紐付け
swarma metric log hook-lab copywriter 127 --metric impressions --exp 3

# CSVから一括インポート
swarma metric import hook-lab metrics.csv

# 記録されたメトリクスを表示
swarma metric show hook-lab
```

CSVフォーマット: `agent,value,metric_name,note`

メトリクスはエージェントのアクティブな実験に自動的に紐付けられる。実験ループは外部メトリクスとLLMスコアの両方が利用可能な場合、両方を使用する。

## プリシード戦略

エージェントはゼロから始めない。各スクワッドには実際のグロース知識（検証済みパターン、アンチパターン、テストすべき仮説）がシードされた`strategy.md`が含まれる。GROWSループがこれを時間とともに洗練していく。

hook-labの戦略からの例:

```markdown
### Validated Patterns

**具体性が勝つ**
- 具体的な数字を含むフックは、曖昧な主張より保存数で2-3倍上回る
- 「スタートアップの47%が」 > 「ほとんどのスタートアップが」

**損失フレーミング > 利得フレーミング**
- 「毎月$Xを失っています」は「毎月$Xを節約できます」よりCTRで上回る
- 例外: 向上心の高いオーディエンスは利得フレーミングにより良く反応する

### テストすべきパターン
- [ ] 一人称の告白 vs 第三者のケーススタディ
- [ ] 時間に紐付いた表現（「2024年に...」） vs 普遍的なフック
```

## 設定としてのチーム

チームは1つのフォルダ。コード不要。

```
teams/my-squad/
├── team.yaml          # ゴール、フロー、スケジュール、予算
├── program.md         # チームのコンテキストと制約
└── agents/
    ├── researcher.yaml
    ├── writer.yaml
    └── strategy.md    # プリシードされたグロース知識
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

モデル、ツール、エキスパートレンズは`config.yaml`で設定する。エージェントはデフォルトを継承するか、エージェントごとにオーバーライドする。

フローDSLはシーケンシャル(`a -> b`)、パラレル(`a -> [b, c, d]`)、およびミックスパイプラインをサポートする。

## 18のスクワッドテンプレート

すぐに使えるスクワッドが[`examples/`](examples/)にあり、それぞれプリシード戦略付き:

```bash
cp -r examples/hook-lab ~/.swarma/instances/default/teams/
swarma cycle hook-lab
```

**コアグロースクワッド:**

| スクワッド | AARRRステージ | テスト内容 | エージェント数 |
|-------|------------|--------------|--------|
| `hook-lab` | 獲得 | 導入文 -- スクロールを止めるもの | 3 |
| `landing-lab` | 獲得 | ランディングページのコピーと構成 | 3 |
| `seo-engine` | 獲得 | 検索プレゼンスとコンテンツランキング | 3 |
| `cold-outbound` | 獲得 | アウトリーチメッセージとシーケンス | 3 |
| `channel-mix` | 獲得 | マルチプラットフォームコンテンツ戦略 | 3 |
| `activation-flow` | 活性化 | サインアップから価値体験までのオンボーディングフロー | 3 |
| `pricing-lab` | 収益 | 価格表示とパッケージング | 3 |
| `retention-squad` | 維持 | 解約シグナルとウィンバックパターン | 3 |
| `referral-engine` | 紹介 | バイラルループと招待メカニクス | 3 |
| `competitive-intel` | -- | 市場モニタリングとポジショニング | 3 |

**2026グロースオプスクワッド:**

| スクワッド | テスト内容 | エージェント数 |
|-------|--------------|--------|
| `faceless-factory` | 自動化されたショートフォーム動画パイプライン | 3 |
| `ad-creative-lab` | パフォーマンスクリエイティブの大規模テスト | 3 |
| `ugc-factory` | ユーザー生成コンテンツのシミュレーション | 3 |
| `programmatic-seo` | 大規模な自動化SEOコンテンツ | 3 |
| `newsletter-engine` | ニュースレターのグロースとリテンション | 3 |
| `acquisition-squad` | 有料+オーガニックの獲得ループ | 3 |
| `community-engine` | コミュニティ主導のグロース自動化 | 3 |
| `agentic-storefront` | AI駆動のコマース最適化 | 3 |

各テンプレートには実験パターンを記述した`program.md`と、開始時のベースラインとなる実際のグロース知識を含む`strategy.md`が付属する。

## QMDナレッジレイヤー

エージェントはstrategy.mdを通じて個別に学習する。これは単一チームの学習だ。チーム*間*で学習するには、[QMD](https://github.com/tobi/qmd)を接続する。QMDはすべてのエージェント出力をインデックス化するナレッジエンジンだ。BM25 + ベクトル + リランク。GPU不要。

```bash
npm install -g @tobilu/qmd
qmd init
qmd serve                          # http://localhost:8181
```

```yaml
# config.yaml
knowledge:
  engine: qmd
  qmd_endpoint: http://localhost:8181/mcp
```

すべてのエージェント出力は自動的にインデックス化される。エージェントは他のエージェントが学んだことを検索できる。GROWSループが共有メモリを獲得する。

実験が**keep**判定を受けると、検証されたパターンはチーム横断の`playbook`コレクションに保存される。すべてのエージェントが他のすべてのチームの検証済みパターンを参照できる。アンチパターン(棄却された実験)も追跡されるため、チームはすでに失敗したことの繰り返しを避けられる。

```bash
# すべての検証済みパターンに対するセマンティック検索
curl localhost:8282/playbook/search?q=hook+specificity
```

これが複利メカニズムだ。チームAが「損失フレーミングが利得フレーミングに勝る」と発見する。チームB(まったく別の実験を実行中)がそのパターンをコンテキストウィンドウで確認し、取り入れる。知識はラチェットのように前進し、後退しない。

## Hermes連携

swarmaは[Hermes](https://github.com/nousresearch/hermes-agent)をオペレーターレイヤーとして連携するよう設計されている。Hermesはクリーンな状態を保つ。方向性を設定し、計画を承認し、「何を学んだか?」と問いかける。swarmaはその下で泥臭い作業を行う。

swarmaは22のツールを備えたMCPサーバーを公開する。接続すれば、Hermesエージェントはスリープ中も実験を実行する完全なグロースチームを手に入れる。

```yaml
# hermes config.yaml
mcp_servers:
  swarma:
    transport: stdio
    command: swarma
    args: ["serve", "--mcp"]
```

オペレーターパターン: Hermesがゴールと制約を定義する。swarmaがチームを生成し、GROWSループを実行し、判定を提示する。Hermesがplaybookを読み、次に何をするかを決定する。オペレーターは実験インフラに直接触れない。

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
swarma serve --port 8282        # 30以上のエンドポイント、OpenAPIドキュメントは/docsで確認
```

### 任意のMCPクライアント

```bash
swarma serve --mcp                     # stdio
swarma serve --mcp --mcp-port 8383     # HTTP
```

**注意**: MCPサブプロセスとして実行する場合、MCP設定の`env`ブロックで`OPENROUTER_API_KEY`を渡すこと。インスタンスの`.env`はサブプロセスに継承されない。

## swarmaが「ではない」もの

- **メモリではない** -- [honcho](https://github.com/plastic-labs/honcho)がメモリを担当する。swarmaは学習ループを担当する。
- **自動化ではない** -- n8n/makeがワークフローを担当する。swarmaは実験を実行する。
- **プロンプトライブラリではない** -- [agency-agents](https://github.com/msitarzewski/agency-agents)には135のテンプレートがある。swarmaはフィードバックループを通じてそれらに何が効くかを教える。
- **オーケストレーションではない** -- crewai/autogenがパイプラインを実行する。swarmaはパイプラインを改善するGROWSループを追加する。

違い: プロンプトテンプレートはエージェントに一度だけ何をすべきかを伝える。swarmaは時間をかけて何が効くかを教える。テンプレートは出発点。playbookがアウトプットだ。

## 立脚する思想

swarmaは3人の人物による3つのアイデアのおかげで存在する:

- **[autoresearch](https://github.com/karpathy/autoresearch)** by Andrej Karpathy -- エージェントが反復的にアプローチを洗練する自動化されたリサーチループのパターン。swarmaはこれを研究論文ではなくグロース実験に適用する。
- **[QMD](https://github.com/tobi/qmd)** by Tobi Lutke ([@tobi](https://x.com/tobi)) -- エージェント間の共有知識。異なる問題に取り組むエージェントが互いから学べるべきだという洞察。swarmaのチーム横断playbookレイヤーはこれを基盤としている。
- **[Hermes](https://github.com/nousresearch/hermes-agent)** by NousResearch ([@NousResearch](https://x.com/NousResearch)) -- オペレーターレイヤー。エージェントがツール使用を通じて専門エージェントチームを指揮できるべきだというアイデア。swarmaはHermesが操作するインフラとして設計されている。

## ロードマップ

**リリース済み:**

- [x] GROWS実験ループ (generate -> run -> observe -> weigh -> stack)
- [x] エキスパート推論レンズ (34の組み合わせ可能な思考フレームワーク)
- [x] ダッシュボードUI (実験ビューア、playbook、戦略進化)
- [x] チームジェネレーター (`swarma team create --from-goal`)
- [x] 外部メトリクス取り込み (`swarma metric log/import/show`)
- [x] 実際のグロース知識によるプリシード戦略ファイル
- [x] `pip install swarma` (PyPI v0.2.0)
- [x] QMDチーム横断接続 (判定 -> playbook -> 共有知識)
- [x] AARRRファネル全体 + 2026グロースオプスをカバーする18のスクワッドテンプレート
- [x] アンチパターン追跡 (discard判定をplaybookに保存)
- [x] `/playbook/search` QMD経由のチーム横断セマンティック検索
- [x] MCPサーバー (22ツール) Hermes / Claude Code / 任意のクライアント向け
- [x] アドホックサイクル用`--topic`フラグ

**次のステップ:**

- [ ] Webhookメトリクス取り込み (リアルタイムアナリティクスコールバック)
- [ ] Hermesスキルハブ + OpenClawマーケットプレイス公開
- [ ] スクワッドマーケットプレイス (検証済みチーム + playbookの共有と発見)
- [ ] HuggingFaceデータセットによるスクワッド知識のシーディング
- [ ] 観測モード実験 (実世界シグナルが主、LLM評価が副)

## コントリビュート

swarmaは初期段階にある。エージェントの実験ループに興味があれば、issueやPRを開いてほしい。

## ライセンス

MIT
