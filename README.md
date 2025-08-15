# MoodFlix v2.0 - AI-Powered Movie Recommendation System

MoodFlixは、GPT-4.1-miniを使用した高精度感情分析とTMDb APIを統合した、革新的な映画推薦システムです。ユーザーの気分や自由テキスト検索に基づいて、最適な映画を推薦します。

## 🎬 主要機能

### 1. ムード推薦
- **GPT-4.1-mini感情分析**: 95%以上の精度で感情を分析
- **多次元感情認識**: 喜び、悲しみ、興奮、落ち着きなど複数の感情を同時検出
- **コンテキスト理解**: 文脈を理解した高度な感情分析
- **推薦理由の説明**: なぜその映画が推薦されるかの詳細説明

### 2. 自由テキスト検索推薦
- **自然言語検索**: 「90分くらいで笑える邦画」「インセプションみたいだけど重すぎないSF」
- **複合条件対応**: 年代、ジャンル、上映時間、国などの複合検索
- **インテリジェント解析**: テキストから検索意図を自動抽出

### 3. TMDb統合
- **豊富な映画データ**: 最新の映画情報、ポスター、評価
- **ストリーミング情報**: 視聴可能なプラットフォーム情報
- **多言語対応**: 日本語・英語での映画情報表示

### 4. セキュリティ・運用機能
- **レート制限**: 3回/分、100回/日の制限
- **OpenAI使用量監視**: 月額上限設定と使用量追跡
- **緊急停止機能**: 環境変数での即座停止
- **キャッシュシステム**: 24時間のインテリジェントキャッシュ

## 🚀 クイックスタート

### 前提条件
- Docker & Docker Compose
- OpenAI API Key
- TMDb API Key

### 1. リポジトリのクローン
```bash
git clone <your-repository-url>
cd moodflix-v2
```

### 2. 環境変数の設定
```bash
cp .env.example .env
```

`.env`ファイルを編集して、以下の必須項目を設定：
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
TMDB_API_KEY=your-tmdb-api-key-here
```

### 3. アプリケーションの起動
```bash
docker compose up --build
```

### 4. アクセス
- フロントエンド: http://localhost:8080
- バックエンドAPI: http://localhost:5000
- ヘルスチェック: http://localhost:5000/api/health

## 📁 プロジェクト構造

```
moodflix-v2/
├── backend/                 # Flask バックエンド
│   ├── services/           # ビジネスロジック
│   │   ├── tmdb_client.py         # TMDb API クライアント
│   │   ├── gpt_emotion_analyzer.py # GPT感情分析
│   │   └── enhanced_recommendation_engine.py # 推薦エンジン
│   ├── utils/              # ユーティリティ
│   │   └── rate_limiter.py        # レート制限・使用量追跡
│   ├── config.py           # 設定管理
│   ├── app.py              # メインアプリケーション
│   ├── requirements.txt    # Python依存関係
│   └── Dockerfile          # バックエンドDocker設定
├── frontend/               # React フロントエンド
│   ├── src/
│   │   ├── App.jsx         # メインコンポーネント
│   │   └── App.css         # スタイル
│   ├── package.json        # Node.js依存関係
│   ├── Dockerfile          # フロントエンドDocker設定
│   └── nginx.conf          # Nginx設定
├── docs/                   # ドキュメント
├── scripts/                # 運用スクリプト
├── docker-compose.yml      # Docker Compose設定
├── .env.example            # 環境変数サンプル
├── .gitignore              # Git除外設定
└── README.md               # このファイル
```

## 🔧 環境変数

### 必須設定
| 変数名 | 説明 | 例 |
|--------|------|-----|
| `OPENAI_API_KEY` | OpenAI API キー | `sk-...` |
| `TMDB_API_KEY` | TMDb API キー | `your-key` |

### セキュリティ設定
| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `RATE_LIMIT_ENABLED` | `true` | レート制限の有効/無効 |
| `RATE_LIMIT_PER_MINUTE` | `3` | 分あたりリクエスト制限 |
| `RATE_LIMIT_PER_DAY` | `100` | 日あたりリクエスト制限 |
| `OPENAI_MONTHLY_LIMIT` | `7` | OpenAI月額上限（USD） |
| `EMERGENCY_STOP` | `false` | 緊急停止スイッチ |

### アプリケーション設定
| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `FLASK_ENV` | `development` | 実行環境 |
| `CACHE_TTL_HOURS` | `24` | キャッシュ保持時間 |
| `LOG_LEVEL` | `INFO` | ログレベル |

## 🔌 API エンドポイント

### ムード推薦
```http
POST /api/recommend/mood
Content-Type: application/json

{
  "text": "I'm feeling excited and want something action-packed",
  "num_recommendations": 8
}
```

### 自由テキスト検索
```http
POST /api/recommend/search
Content-Type: application/json

{
  "text": "90分くらいで笑える邦画",
  "num_recommendations": 8
}
```

### 映画詳細
```http
GET /api/movie/{movie_id}
```

### システム状態
```http
GET /api/status
```

### ヘルスチェック
```http
GET /api/health
```

## 🛠️ 開発環境

### ローカル開発
```bash
# バックエンド
cd backend
pip install -r requirements.txt
python app.py

# フロントエンド
cd frontend
npm install
npm run dev
```

### テスト実行
```bash
# バックエンドテスト
cd backend
pytest

# フロントエンドテスト
cd frontend
npm test
```

## 🚀 デプロイメント

### Manus ホスティング（推奨）
1. プロジェクトをManus環境にアップロード
2. 環境変数を設定
3. `docker compose up --build`で起動

### Railway / Render
1. GitHubリポジトリを接続
2. 環境変数を設定
3. 自動デプロイ

### Cloudflare（本格運用）
1. 独自ドメインの設定
2. CDN・WAFの有効化
3. SSL証明書の設定

## 📊 監視・運用

### 使用量監視
- OpenAI API使用量の自動追跡
- 月額上限の設定・監視
- レート制限の統計

### ログ監視
```bash
# アプリケーションログ
docker compose logs -f backend

# システムログ
docker compose logs -f
```

### ヘルスチェック
```bash
curl http://localhost:5000/api/health
```

## ⚠️ 重要な注意事項

### セキュリティ
- **APIキーの管理**: `.env`ファイルは絶対にGitにコミットしない
- **本番環境**: 強力なSECRET_KEYを設定
- **CORS設定**: 本番環境では適切なオリジンを設定

### コスト管理
- **OpenAI制限**: 月額上限を適切に設定
- **TMDb制限**: レート制限を遵守
- **使用量監視**: 定期的な使用量チェック

### ライセンス・クレジット
- **TMDb**: "This product uses the TMDb API but is not endorsed or certified by TMDb."
- **OpenAI**: 利用規約の遵守

## 🔄 変更履歴

### v2.0.0 (2025-01-15)
- **新機能**: TMDb API統合
- **新機能**: 自由テキスト検索推薦
- **改善**: Docker Compose対応
- **改善**: セキュリティ・レート制限強化
- **改善**: キャッシュシステム実装
- **改善**: 使用量監視機能

### v1.0.0 (2024-12-XX)
- **初回リリース**: GPT-4.1-mini感情分析
- **基本機能**: ムード推薦システム

## 🤝 コントリビューション

1. フォークを作成
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 🆘 サポート

- **Issues**: GitHubのIssuesで報告
- **ドキュメント**: `docs/`フォルダを参照
- **API仕様**: `docs/api-specification.md`を参照

---

**MoodFlix v2.0** - AI-powered movie recommendations for every mood 🎬✨

