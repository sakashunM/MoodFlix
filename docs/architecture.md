# MoodFlix アーキテクチャ設計書

## システム概要

MoodFlixは、AI感情分析とTMDb統合による映画推薦システムです。マイクロサービス的なアーキテクチャを採用し、Docker Composeによる統合運用を実現しています。

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   React App     │  │   Nginx Proxy   │  │  Static CDN  │ │
│  │   (Port 3000)   │  │   (Port 80)     │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   Flask API     │  │  Rate Limiter   │  │   Logger     │ │
│  │   (Port 5000)   │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Services Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Emotion Analyzer│  │ TMDb Client     │  │ Recommendation│ │
│  │ (GPT-4.1-mini)  │  │                 │  │ Engine        │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │     Redis       │  │   File Cache    │  │   Logs       │ │
│  │   (Cache)       │  │                 │  │              │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                            │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   OpenAI API    │  │   TMDb API      │                   │
│  │  (GPT-4.1-mini) │  │                 │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. フロントエンド層

#### React Application
- **技術**: React 18 + Vite
- **UI**: Tailwind CSS + Lucide Icons
- **状態管理**: React Hooks
- **特徴**:
  - レスポンシブデザイン
  - リアルタイムフィードバック
  - エラーハンドリング
  - ローディング状態管理

#### Nginx Proxy
- **役割**: 静的ファイル配信、リバースプロキシ
- **設定**:
  - Gzip圧縮
  - セキュリティヘッダー
  - キャッシュ制御
  - SPA対応ルーティング

### 2. バックエンド層

#### Flask API Server
- **技術**: Flask 3.0 + Python 3.11
- **特徴**:
  - RESTful API設計
  - 構造化ログ（structlog）
  - CORS対応
  - ヘルスチェック機能

#### Rate Limiter
- **実装**: Redis + メモリベース
- **機能**:
  - 分/日単位の制限
  - OpenAI使用量追跡
  - 緊急停止機能
  - 使用量統計

### 3. サービス層

#### GPT Emotion Analyzer
```python
class GPTEmotionAnalyzer:
    - analyze_emotion(text) -> Analysis
    - _parse_analysis_result(response)
    - _estimate_cost(tokens)
```

#### TMDb Client
```python
class TMDbClient:
    - search_movies(query) -> List[Movie]
    - get_movie_details(id) -> Movie
    - discover_movies(**filters) -> List[Movie]
    - _rate_limit()
    - _cache_management()
```

#### Enhanced Recommendation Engine
```python
class EnhancedRecommendationEngine:
    - recommend_by_mood_analysis(analysis) -> List[Recommendation]
    - recommend_by_text_search(text) -> List[Recommendation]
    - _calculate_mood_score(movie, moods)
    - _generate_match_reasons(movie, matches)
```

### 4. データ層

#### Redis Cache
- **用途**:
  - API レスポンスキャッシュ
  - レート制限カウンター
  - 使用量統計
- **TTL設定**:
  - 映画詳細: 24時間
  - 検索結果: 1時間
  - 設定情報: 1週間

#### File System
- **ログファイル**: 構造化JSON形式
- **設定ファイル**: 環境変数ベース
- **静的ファイル**: React build成果物

## データフロー

### 1. ムード推薦フロー

```
User Input → Frontend → Backend API → Emotion Analyzer → OpenAI API
                                   ↓
TMDb Client → TMDb API → Recommendation Engine → Response Cache
                                   ↓
Backend API → Frontend → User Display
```

### 2. 自由テキスト検索フロー

```
Search Text → Frontend → Backend API → Text Parser → Search Criteria
                                    ↓
TMDb Client → TMDb API → Movie Results → Recommendation Engine
                                    ↓
Score Calculation → Response Cache → Backend API → Frontend
```

### 3. キャッシュフロー

```
Request → Cache Check → Cache Hit? → Return Cached Data
                     ↓ (Cache Miss)
External API → Process Data → Store in Cache → Return Data
```

## セキュリティ設計

### 1. API セキュリティ
- **レート制限**: 分/日単位の制限
- **CORS設定**: 許可されたオリジンのみ
- **入力検証**: 全入力の検証・サニタイズ
- **エラーハンドリング**: 情報漏洩防止

### 2. 秘密情報管理
- **環境変数**: 全ての秘密情報
- **Docker Secrets**: 本番環境での秘密管理
- **Git除外**: .envファイルの除外

### 3. 運用セキュリティ
- **緊急停止**: 環境変数での即座停止
- **使用量監視**: OpenAI/TMDb使用量追跡
- **ログ監視**: 異常アクセスの検出

## スケーラビリティ設計

### 1. 水平スケーリング
```
Load Balancer → Multiple Backend Instances → Shared Redis Cache
```

### 2. キャッシュ戦略
- **L1 Cache**: アプリケーション内メモリ
- **L2 Cache**: Redis分散キャッシュ
- **L3 Cache**: CDN（静的ファイル）

### 3. データベース設計（将来拡張）
```
User Data → PostgreSQL → Read Replicas
Recommendations → Time Series DB
Analytics → Data Warehouse
```

## 監視・運用設計

### 1. ヘルスチェック
```python
/api/health:
  - TMDb API接続性
  - OpenAI API接続性
  - Redis接続性
  - システムリソース
```

### 2. メトリクス収集
- **アプリケーションメトリクス**:
  - リクエスト数/レスポンス時間
  - エラー率
  - API使用量
- **システムメトリクス**:
  - CPU/メモリ使用率
  - ディスク使用量
  - ネットワーク使用量

### 3. ログ管理
```python
Structured Logging:
  - Request/Response logs
  - Error logs with stack traces
  - Performance metrics
  - Security events
```

## デプロイメント設計

### 1. 開発環境
```yaml
docker-compose.yml:
  - Hot reload enabled
  - Debug mode
  - Local Redis
  - Development APIs
```

### 2. ステージング環境
```yaml
docker-compose.staging.yml:
  - Production-like setup
  - External Redis
  - SSL termination
  - Monitoring enabled
```

### 3. 本番環境
```yaml
Kubernetes/Docker Swarm:
  - Multiple replicas
  - Load balancing
  - Auto-scaling
  - Health checks
  - Rolling updates
```

## パフォーマンス最適化

### 1. フロントエンド最適化
- **Code Splitting**: ルートベース分割
- **Lazy Loading**: 画像・コンポーネント
- **Bundle Optimization**: Tree shaking
- **CDN**: 静的ファイル配信

### 2. バックエンド最適化
- **Connection Pooling**: データベース接続
- **Async Processing**: 非同期処理
- **Caching Strategy**: 多層キャッシュ
- **Rate Limiting**: API保護

### 3. データベース最適化
- **Indexing**: 検索性能向上
- **Query Optimization**: N+1問題回避
- **Connection Pooling**: 接続効率化
- **Read Replicas**: 読み取り負荷分散

## 障害対応設計

### 1. 障害検出
- **ヘルスチェック**: 定期的な生存確認
- **アラート**: 閾値ベースの通知
- **ログ監視**: エラーパターン検出

### 2. 障害回復
- **Auto Restart**: コンテナ自動再起動
- **Circuit Breaker**: 外部API障害対応
- **Graceful Degradation**: 機能縮退運転

### 3. バックアップ・復旧
- **データバックアップ**: 定期的なデータ保存
- **設定バックアップ**: 環境設定の保存
- **災害復旧**: 迅速な復旧手順

## 今後の拡張計画

### 1. 機能拡張
- **ユーザーアカウント**: 個人化機能
- **視聴履歴**: 推薦精度向上
- **ソーシャル機能**: レビュー・評価
- **多言語対応**: 国際化

### 2. 技術拡張
- **機械学習**: 推薦アルゴリズム改善
- **リアルタイム**: WebSocket通信
- **モバイルアプリ**: React Native
- **API Gateway**: マイクロサービス化

### 3. 運用拡張
- **CI/CD**: 自動デプロイ
- **監視強化**: APM導入
- **セキュリティ**: WAF・DDoS対策
- **コンプライアンス**: GDPR対応

