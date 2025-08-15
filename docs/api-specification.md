# MoodFlix API 仕様書

## 概要

MoodFlix APIは、AI感情分析とTMDb統合による映画推薦システムのRESTful APIです。

**Base URL**: `http://localhost:5000` (開発環境)

## 認証

現在のバージョンでは認証は不要ですが、レート制限が適用されます。

## レート制限

- **分あたり制限**: 3リクエスト/分
- **日あたり制限**: 100リクエスト/日
- **OpenAI月額制限**: 設定可能（デフォルト: $7）

制限に達した場合、`429 Too Many Requests`が返されます。

## エンドポイント

### 1. ヘルスチェック

システムの状態を確認します。

```http
GET /api/health
```

#### レスポンス例

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "tmdb": "healthy",
    "openai": "healthy",
    "redis": "healthy"
  },
  "version": "2.0.0"
}
```

#### ステータスコード
- `200`: システム正常
- `503`: システム異常

---

### 2. ムード推薦

感情分析に基づく映画推薦を取得します。

```http
POST /api/recommend/mood
```

#### リクエストボディ

```json
{
  "text": "I'm feeling excited and want something action-packed",
  "num_recommendations": 8
}
```

#### パラメータ

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `text` | string | ✓ | 感情や気分を表すテキスト |
| `num_recommendations` | integer | - | 推薦数（1-20、デフォルト: 8） |

#### レスポンス例

```json
{
  "analysis": {
    "emotions": {
      "excitement": 0.8,
      "joy": 0.6,
      "energy": 0.7
    },
    "moods": {
      "action": 0.9,
      "adventure": 0.7,
      "energetic": 0.8
    },
    "confidence": 0.95,
    "method": "gpt-4.1-mini",
    "reasoning": "The user explicitly expresses excitement and desire for action-packed content..."
  },
  "recommendations": [
    {
      "movie": {
        "id": 550,
        "title": "Fight Club",
        "original_title": "Fight Club",
        "overview": "A ticking-time-bomb insomniac...",
        "release_date": "1999-10-15",
        "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
        "backdrop_path": "/87hTDiay2N2qWyX4Ds7ybXi9h8I.jpg",
        "backdrop_url": "https://image.tmdb.org/t/p/w1280/87hTDiay2N2qWyX4Ds7ybXi9h8I.jpg",
        "genres": ["Drama", "Thriller"],
        "vote_average": 8.4,
        "vote_count": 26280,
        "popularity": 61.416,
        "runtime": 139,
        "adult": false,
        "original_language": "en"
      },
      "score": 85,
      "match_reasons": [
        "Matches your action mood",
        "Suits your excitement feeling",
        "Highly rated film"
      ],
      "mood_matches": {
        "action": 0.8,
        "intense": 0.7
      },
      "emotion_matches": {
        "excitement": 0.6
      }
    }
  ],
  "metadata": {
    "total_found": 8,
    "timestamp": "2025-01-15T10:30:00Z",
    "method": "mood_analysis"
  }
}
```

#### ステータスコード
- `200`: 成功
- `400`: 不正なリクエスト
- `429`: レート制限超過
- `500`: サーバーエラー

---

### 3. 自由テキスト検索推薦

自由テキストに基づく映画推薦を取得します。

```http
POST /api/recommend/search
```

#### リクエストボディ

```json
{
  "text": "90分くらいで笑える邦画",
  "num_recommendations": 8
}
```

#### パラメータ

| フィールド | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `text` | string | ✓ | 検索条件を表すテキスト |
| `num_recommendations` | integer | - | 推薦数（1-20、デフォルト: 8） |

#### レスポンス例

```json
{
  "search_query": "90分くらいで笑える邦画",
  "recommendations": [
    {
      "movie": {
        "id": 12345,
        "title": "アフタースクール",
        "original_title": "After School",
        "overview": "中学時代の同級生たちが巻き込まれる騙し合いの物語...",
        "release_date": "2008-05-24",
        "poster_url": "https://image.tmdb.org/t/p/w500/...",
        "genres": ["Comedy", "Mystery"],
        "vote_average": 7.2,
        "runtime": 100,
        "original_language": "ja"
      },
      "score": 78,
      "match_reasons": [
        "Matches comedy genre",
        "Runtime close to 90 minutes",
        "Japanese film"
      ],
      "mood_matches": {},
      "emotion_matches": {}
    }
  ],
  "metadata": {
    "total_found": 6,
    "timestamp": "2025-01-15T10:30:00Z",
    "method": "text_search"
  }
}
```

#### ステータスコード
- `200`: 成功
- `400`: 不正なリクエスト
- `429`: レート制限超過
- `500`: サーバーエラー

---

### 4. 映画詳細

特定の映画の詳細情報を取得します。

```http
GET /api/movie/{movie_id}
```

#### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `movie_id` | integer | ✓ | TMDb映画ID |

#### レスポンス例

```json
{
  "movie": {
    "id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "overview": "A ticking-time-bomb insomniac...",
    "release_date": "1999-10-15",
    "poster_url": "https://image.tmdb.org/t/p/w500/...",
    "backdrop_url": "https://image.tmdb.org/t/p/w1280/...",
    "genres": ["Drama", "Thriller"],
    "vote_average": 8.4,
    "vote_count": 26280,
    "popularity": 61.416,
    "runtime": 139,
    "adult": false,
    "original_language": "en"
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### ステータスコード
- `200`: 成功
- `404`: 映画が見つからない
- `429`: レート制限超過
- `500`: サーバーエラー

---

### 5. 人気映画

人気映画のリストを取得します。

```http
GET /api/movies/popular?page=1
```

#### クエリパラメータ

| パラメータ | 型 | 必須 | 説明 |
|------------|-----|------|------|
| `page` | integer | - | ページ番号（1-10、デフォルト: 1） |

#### レスポンス例

```json
{
  "movies": [
    {
      "id": 550,
      "title": "Fight Club",
      "overview": "A ticking-time-bomb insomniac...",
      "poster_url": "https://image.tmdb.org/t/p/w500/...",
      "vote_average": 8.4,
      "genres": ["Drama", "Thriller"]
    }
  ],
  "page": 1,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

### 6. システム状態

システムの詳細状態と使用量情報を取得します。

```http
GET /api/status
```

#### レスポンス例

```json
{
  "system": {
    "status": "operational",
    "emergency_stop": false,
    "rate_limiting": true,
    "version": "2.0.0"
  },
  "usage": {
    "openai": {
      "monthly_cost": 2.45,
      "monthly_limit": 7.0,
      "within_limit": true,
      "requests_this_month": 123,
      "tokens_this_month": 45000
    }
  },
  "limits": {
    "requests_per_minute": 3,
    "requests_per_day": 100
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## エラーレスポンス

### 標準エラー形式

```json
{
  "error": "Error type",
  "message": "Human readable error message",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### レート制限エラー

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Limit: 3 per minute.",
  "current_count": 4,
  "limit": 3,
  "window": "1 minute",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### OpenAI制限エラー

```json
{
  "error": "Monthly OpenAI limit exceeded",
  "message": "Monthly spending limit of $7 exceeded.",
  "current_cost": 7.25,
  "limit": 7.0,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## データ型

### Movie Object

```typescript
interface Movie {
  id: number;
  title: string;
  original_title: string;
  overview: string;
  release_date: string;
  poster_path: string | null;
  poster_url: string | null;
  backdrop_path: string | null;
  backdrop_url: string | null;
  genre_ids: number[];
  genres: string[];
  vote_average: number;
  vote_count: number;
  popularity: number;
  runtime: number | null;
  adult: boolean;
  original_language: string;
}
```

### Recommendation Object

```typescript
interface Recommendation {
  movie: Movie;
  score: number; // 0-100
  match_reasons: string[];
  mood_matches: Record<string, number>;
  emotion_matches: Record<string, number>;
}
```

### Analysis Object

```typescript
interface Analysis {
  emotions: Record<string, number>;
  moods: Record<string, number>;
  confidence: number; // 0-1
  method: string;
  reasoning?: string;
}
```

## 使用例

### cURL

```bash
# ムード推薦
curl -X POST http://localhost:5000/api/recommend/mood \
  -H "Content-Type: application/json" \
  -d '{"text": "I want something romantic for date night"}'

# 自由テキスト検索
curl -X POST http://localhost:5000/api/recommend/search \
  -H "Content-Type: application/json" \
  -d '{"text": "90分くらいで笑える邦画"}'

# ヘルスチェック
curl http://localhost:5000/api/health
```

### JavaScript

```javascript
// ムード推薦
const response = await fetch('/api/recommend/mood', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'I want something romantic for date night',
    num_recommendations: 8
  })
});

const data = await response.json();
```

### Python

```python
import requests

# ムード推薦
response = requests.post('http://localhost:5000/api/recommend/mood', 
  json={
    'text': 'I want something romantic for date night',
    'num_recommendations': 8
  }
)

data = response.json()
```

## 注意事項

1. **レート制限**: 適切な間隔でリクエストを送信してください
2. **エラーハンドリング**: 429、500エラーに対する適切な処理を実装してください
3. **キャッシュ**: 同じリクエストは24時間キャッシュされます
4. **TMDbクレジット**: TMDb APIを使用している旨の表記が必要です

