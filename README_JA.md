# swarma

[English](README.md) | [中文](README_CN.md) | **日本語**

自律的に学習するエージェントチーム。

---

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

swarma は、実験を繰り返しながら自律的に戦略を改善するエージェントチームを構築するフレームワークです。各エージェントは1つの指標、1つの編集可能な戦略ファイル、そして実測結果に基づいて前進し続ける学習ループを持ちます。

これは [Karpathy の autoresearch パターン](https://github.com/karpathy/autoresearch) をエージェントチームに適用したものです。ただし、エージェントが最適化するのはトレーニングではなく、実際のワークフローです。

## 仕組み

```
strategy.md → 実行 → 計測 → 判定 → 更新された strategy.md
     ↑                                              |
     └──────────────────────────────────────────────┘
```

1. 各エージェントは実行前に自身の `strategy.md` を読み込む
2. アウトプットを生成（コンテンツ、リサーチ、分析 -- チームの役割に応じて）
3. 目標指標に対してアウトプットを評価
4. スコアを `results.tsv` に記録
5. 十分なサンプル数に達したら判定を下す：**保持 (keep)**、**破棄 (discard)**、**不確定 (inconclusive)**
6. 学んだことを `strategy.md` に反映
7. 次のサイクルは進化した戦略で開始

## クイックスタート

```bash
git clone https://github.com/glitch-rabin/swarma.git
cd swarma
pip install -e .
```

```bash
# スターターチーム付きでインスタンスを初期化
swarma init

# API キーを設定
echo "OPENROUTER_API_KEY=sk-or-..." > ~/.swarma/instances/default/.env

# 1サイクル実行
swarma run --once

# またはスケジューリング + API サーバー付きで継続実行
swarma run --port 8000
```

## 必要なもの

- Python 3.11+
- [OpenRouter](https://openrouter.ai/) の API キー
- 以上。GPU不要、PostgreSQL不要、Docker不要。

SQLite で状態管理、Markdown ファイルでナレッジ管理。ノートPCや月額$5のVPSで動作します。

## チーム = 設定ファイル

チームはYAML設定ファイルを含むフォルダです。コードは不要。

```
teams/content-ops/
├── team.yaml              # 目標、フロー、スケジュール、予算
├── program.md             # チームのコンテキストと制約
└── agents/
    ├── researcher.yaml    # モデル、指標、指示
    └── writer.yaml
```

**team.yaml**
```yaml
name: Content Operations
goal: produce practitioner-grade content worth saving.
flow: "researcher -> writer"
schedule: "0 7 * * *"     # 毎日午前7時
budget_monthly: 50.0
```

**エージェント設定**
```yaml
id: writer
name: Content Writer
model:
  model_id: qwen/qwen3.5-plus-02-15
  max_tokens: 1500
  temperature: 0.7
instructions: |
  turn research into a linkedin post. max 200 words.
  hook in the first line. practitioner voice. no emojis.
metric:
  name: content_quality
  target: 8.0
experiment_config:
  min_sample_size: 3
  auto_propose: true
```

## サンプルチーム

14のすぐに使えるチーム設定が [`examples/`](examples/) にあります（機能別に分類）：

| カテゴリ | チーム | フロー | 内容 |
|---------|--------|--------|------|
| **コンテンツ & グロース** | `content-ops` | researcher -> writer | リサーチ + LinkedIn投稿 |
| | `social-growth` | researcher -> growth-lead -> [linkedin, twitter, newsletter] | マルチプラットフォーム配信 |
| | `seo-lab` | keyword-researcher -> content-writer -> seo-auditor | SEOコンテンツ実験 |
| | `thought-leadership` | research-analyst -> essay-writer -> editor | 長文オーソリティコンテンツ |
| **リサーチ & インテリジェンス** | `market-intel` | scanner -> analyst -> briefer | 競合インテリジェンス |
| | `trend-scout` | monitor -> analyst -> reporter | 新興トレンド検出 |
| | `crypto-research` | data-collector -> analyst -> strategist | DeFi市場分析 |
| **コンバージョン** | `email-ops` | researcher -> copywriter -> subject-line-tester | メールキャンペーン最適化 |
| | `landing-copy` | researcher -> copywriter -> critic | ランディングページA/Bテスト |
| **オペレーション** | `quality-lab` | auditor | クロスチーム品質評価 |
| | `model-lab` | prompt-engineer -> evaluator | モデル比較ベンチマーク |
| | `cost-optimizer` | tester -> analyst | 品質基準を維持しつつコスト最小化 |
| **専門** | `dev-rel` | docs-researcher -> tutorial-writer -> code-reviewer | 開発者チュートリアル |
| | `product-growth` | analyst -> hypothesis-generator -> experiment-designer | グロース実験設計 |

各チームはフォルダ1つ。インスタンスにコピーしてカスタマイズできます。`swarma init --template content-ops` で任意のサンプルから初期化。

## 実験ループ

`metric` が定義されたエージェントには自動的に学習ループが付与されます：

```
teams/content-ops/results/writer/
├── strategy.md              # 編集可能、時間とともに進化
├── results.tsv              # 追記専用のスコアログ
└── experiments/
    └── exp-001.md           # 詳細な実験記録
```

**strategy.md** は実験ごとに更新されます：
```markdown
# 現在の戦略

戦略未設定。最初の実験を待機中。

## 不確定 (実験 2)
試行：各投稿に具体的なネクストステップを追加 -- 有意な変化なし (平均=7.9 vs ベースライン=7.8)
> 次回：業界ベンチマークとの比較で追加コンテキストを取得

## 検証済み (実験 5)
逆張りフック + 1行目に具体的な数字
> ベースラインから23%改善。このパターンを保持。
```

プレイブックは成長し続け、チームは賢くなり続けます。手を加える必要はありません。

## 計測

デフォルトでは、エージェントは低コストなLLMコールで自己評価を行います。プロトタイピングやループの起動には十分です。

本番環境では、実際のシグナルを接続します：

```yaml
# エージェント設定 -- 外部指標コールバック
metric:
  name: linkedin_saves
  target: 50
  source: webhook    # POST {output_id, score} を受付
```

```bash
# 実際の分析データをループにプッシュ
curl -X POST http://localhost:8282/metrics \
  -d '{"agent": "writer", "output_id": "cycle-001", "score": 47}'
```

自己評価で素早くイテレーション。外部シグナルで本当に重要なものを最適化。

## フロー DSL

エージェントパイプラインを定義：

```yaml
# 逐次実行
flow: "researcher -> writer"

# 並列実行
flow: "researcher -> [linkedin-writer, twitter-writer, visual-designer]"

# 混合
flow: "[research-analyst, intelligence-agent] -> growth-lead -> [linkedin-writer, twitter-writer] -> analytics"
```

並列ステップは `asyncio.gather()` で実行。ステップNの出力がステップN+1のコンテキストになります。

## マルチモデルルーティング

swarma は [OpenRouter](https://openrouter.ai/) を通じてタスクに最適なモデルにルーティングします。300以上のモデル、トークン単位の課金。

```yaml
# config.yaml のデフォルトルーティングテーブル（エージェントごとにオーバーライド可）
models:
  routing:
    cheap: mistralai/mistral-nemo
    writing: qwen/qwen3.5-plus-02-15
    research: perplexity/sonar-pro
    reasoning: deepseek/deepseek-r1
    planning: anthropic/claude-sonnet-4-6
```

各エージェントは設定でモデルをオーバーライドできます。コストはエージェント別、チーム別、日別で追跡されます。

## 共有ナレッジ + QMD

全チームがナレッジストアを共有します。エージェントはYAMLフロントマター付きのMarkdownファイルとしてアーティファクトを書き出し、検索用にインデックスされます。

デフォルトはSQLiteメタデータクエリ -- ゼロセットアップで機能します。本番環境では [QMD](https://github.com/tobi/qmd)（Tobi Lutke 開発）を接続して完全なセマンティック検索を有効化：

```yaml
# config.yaml
knowledge:
  qmd_endpoint: http://localhost:8181    # BM25 + ベクトル + リランク
  collections: [research, content, experiments, briefs]
```

QMD接続時、エージェントが利用できる機能：
- **BM25 + ベクトル + リランク** 全チームの全アーティファクトを横断検索
- **コレクション限定クエリ**（例：`research` アーティファクトのみ検索）
- **クロスチームナレッジ転送** -- チームAのリサーチがチームBの意思決定に自動反映

ナレッジはインスタンス全体で蓄積されていきます。QMD未接続でも動作します -- よりシンプルなメタデータマッチングにフォールバック。

## ランタイムアダプター

エージェントはLLMコールに限りません。swarma は4つのランタイムをサポート：

| ランタイム | ユースケース | 設定 |
|-----------|-------------|------|
| `llm`（デフォルト） | OpenRouter経由の直接LLMコール | エージェントYAMLのモデル設定 |
| `hermes` | [Hermes Agent](https://github.com/nousresearch/hermes-agent)（フルツールアクセス） | endpoint + api_key |
| `http` | JSONを受け付ける任意のHTTPエンドポイント | endpoint + headers |
| `process` | ローカルCLIコマンド、stdin/stdout JSON | command + timeout |

## インテグレーション

swarma は2つの方向でスタックと接続します：エージェントはランタイムアダプター経由で**外部を呼び出し**、外部システムはMCPまたはREST経由で**内部に接続**します。

**Hermes Agent** -- 最も深い統合。Hermesエージェントはフルツールアクセスを取得し、swarma がオーケストレーションと学習を担当します。逆方向も可能：Hermesをswarma の MCPサーバーに接続して Telegram/Discord からサイクルをトリガー。

**Claude Code / Claude Desktop** -- swarma をMCPサーバーとして追加。Claude がサイクル実行、実験確認、プレイブック閲覧、計画承認のツールを取得します。

```json
{
  "mcpServers": {
    "swarma": {
      "command": "swarma",
      "args": ["serve", "--mcp", "--instance", "my-swarm"]
    }
  }
}
```

**任意のMCPクライアント** -- stdio または HTTP トランスポート：

```bash
swarma serve --mcp                          # stdio
swarma serve --mcp --mcp-port 8383          # HTTP
```

**REST API** -- HTTP経由でフルコントロール。OpenAPIドキュメントは `/docs`。

```bash
swarma serve --port 8282
```

## アーキテクチャ

```
swarma/
├── core/           # エージェント、サイクルランナー、実験ループ、状態、設定、ナレッジ
├── flow/           # DSLパーサー + 非同期エグゼキューター
├── adapters/       # llm、hermes、http、process ランタイム
├── tools/          # 3層レジストリ（インスタンス > チーム > エージェント）
├── experts/        # 推論フレームワークカタログ + コンポーザー
├── server/         # FastAPI REST + MCPプロトコルサーバー
└── cli/            # init、run、serve、status、team、tool コマンド
```

**状態**: SQLite (outputs, experiments, cost_log, agent_runs, pending_plans, artifact_log, task_queue)

**ナレッジ**: ディスク上のMarkdownファイル、SQLiteでインデックス、オプションでQMD検索

**スケジューリング**: APScheduler による cron ベースのチームサイクル + イベント駆動のハートビートキュー

## 設計思想

**デフォルトは自己評価。** エージェントは低コストモデルで自身のアウトプットを評価します。意図的に不完全です -- ゼロセットアップでループを動かすため。本番環境では外部シグナル（アナリティクス、人間の評価、APIメトリクス）を接続すべきです。ループの仕組みは同じで、シグナルソースだけが異なります。

**Markdownファイルで保存。** 戦略ファイル、ナレッジアーティファクト、実験ログ -- すべて可読、編集可能、diff可能、Git フレンドリー。独自フォーマットなし、データベースロックインなし。`cat strategy.md` でエージェントが知っていることがすべてわかります。

**プロバイダーAPI直接接続ではなくOpenRouter。** APIキー1つで300以上のモデル、トークン単位の課金。YAMLの文字列を変えるだけでモデル切り替え。SDK変更不要、認証情報のローテーション不要。

**YAMLチーム、コード不要。** チーム定義にPythonは不要です。LLMの補助があれば、非エンジニアでもチーム設定を作成・変更・理解できます。フレームワークが配線を担当します。

**予算追跡（強制なし）。** コストはエージェント別、チーム別、日別で追跡。team config の `budget_monthly` は現在情報提供のみ -- サイクルを強制停止しません。強制は計画中ですが未出荷。`swarma status` で支出を確認。

**コンテキストウィンドウ管理はまだない。** 戦略ファイル、ナレッジ検索、エキスパートレンズがプロンプト内でトークンを奪い合います。現時点では戦略ファイルを短く、ナレッジクエリを的確に保ってください。階層型コンテキストローディング (L0/L1/L2) はロードマップにあります。

## swarma ではないもの

- **チャットボットフレームワークではない** -- エージェントはスケジュールに従って自律実行し、ユーザーメッセージに応答するものではない
- **メモリエンジンではない** -- [Honcho](https://github.com/plastic-labs/honcho) がメモリを担当。swarma はオーケストレーション + 学習。
- **プロンプトライブラリではない** -- [agency-agents](https://github.com/msitarzewski/agency-agents) は135のエージェントテンプレートを持つ。swarma はそれらを実行し、何が効果的かを学習させる。
- **シミュレーションエンジンではない** -- [MiroFish](https://github.com/666ghj/MiroFish) は群体シミュレーション。swarma は実際のワークフローを最適化する。

## ロードマップ

- [x] チームテンプレート（14サンプル：コンテンツ、リサーチ、コンバージョン、オペレーション、専門）
- [ ] ダッシュボードUI（実験ビューワー、プレイブック、エージェント詳細）
- [ ] 外部メトリクス取り込み（webhooks、アナリティクスコールバック）
- [ ] Hermes Agent インテグレーションパッケージ
- [ ] 階層型コンテキストローディング（L0/L1/L2、[OpenViking](https://github.com/volcengine/OpenViking) にインスパイア）
- [ ] PyPI 公開 `pip install swarma`

## コントリビューション

swarma は初期段階です。エージェント学習ループ、グロース実験フレームワーク、マルチモデルオーケストレーションに興味がある方は、Issue や PR を歓迎します。

## ライセンス

MIT
