# MoodFlix デプロイメントガイド

## 概要

このガイドでは、MoodFlixを様々な環境にデプロイする方法を説明します。開発環境からManusホスティング、そして本格的なクラウドデプロイまでをカバーします。

## 前提条件

### 必須要件
- Docker & Docker Compose
- OpenAI API Key
- TMDb API Key
- Git

### 推奨要件
- 4GB以上のRAM
- 10GB以上のディスク容量
- 安定したインターネット接続

## 1. ローカル開発環境

### セットアップ手順

1. **リポジトリのクローン**
```bash
git clone <your-repository-url>
cd moodflix-v2
```

2. **環境変数の設定**
```bash
cp .env.example .env
```

`.env`ファイルを編集：
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
TMDB_API_KEY=your-tmdb-api-key-here
FLASK_ENV=development
FLASK_DEBUG=true
RATE_LIMIT_ENABLED=false
```

3. **Docker Composeでの起動**
```bash
docker compose up --build
```

4. **アクセス確認**
- フロントエンド: http://localhost:8080
- バックエンドAPI: http://localhost:5000
- ヘルスチェック: http://localhost:5000/api/health

### 開発用コマンド

```bash
# ログの確認
docker compose logs -f

# 特定のサービスのログ
docker compose logs -f backend

# サービスの再起動
docker compose restart backend

# 停止
docker compose down

# 完全なクリーンアップ
docker compose down -v --rmi all
```

## 2. Manusホスティング環境

### 特徴
- 簡単なデプロイ
- 一時的なURL提供
- 開発・テスト用途に最適

### デプロイ手順

1. **プロジェクトのアップロード**
```bash
# Manusファイルマネージャーでプロジェクトをアップロード
# または git clone を使用
```

2. **環境変数の設定**
```bash
# Manus環境で .env ファイルを作成
cp .env.example .env
nano .env
```

3. **Docker Composeでの起動**
```bash
docker compose up --build -d
```

4. **外部公開**
```bash
# Manusのポート公開機能を使用
# または service_expose_port ツールを使用
```

### Manus固有の設定

```env
# .env for Manus
FLASK_ENV=production
FLASK_DEBUG=false
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=https://your-manus-url.manusvm.computer
```

## 3. Railway デプロイ

### 特徴
- Git連携による自動デプロイ
- 無料枠あり
- 簡単なスケーリング

### デプロイ手順

1. **Railwayアカウント作成**
   - https://railway.app でアカウント作成

2. **GitHubリポジトリ接続**
   - Railway ダッシュボードで「New Project」
   - GitHubリポジトリを選択

3. **環境変数の設定**
   - Railway ダッシュボードで環境変数を設定
   ```
   OPENAI_API_KEY=sk-your-key
   TMDB_API_KEY=your-key
   FLASK_ENV=production
   REDIS_URL=redis://redis:6379/0
   ```

4. **railway.json の作成**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Railway用 Docker設定

```dockerfile
# Dockerfile.railway
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build
COPY frontend/dist/ static/

EXPOSE $PORT

CMD python app.py
```

## 4. Render デプロイ

### 特徴
- 無料SSL証明書
- 自動スケーリング
- PostgreSQL統合

### デプロイ手順

1. **Renderアカウント作成**
   - https://render.com でアカウント作成

2. **Web Service作成**
   - 「New Web Service」を選択
   - GitHubリポジトリを接続

3. **設定**
```yaml
# render.yaml
services:
  - type: web
    name: moodflix-backend
    env: python
    buildCommand: "cd backend && pip install -r requirements.txt"
    startCommand: "cd backend && python app.py"
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: TMDB_API_KEY
        sync: false
      - key: FLASK_ENV
        value: production
```

4. **環境変数設定**
   - Render ダッシュボードで環境変数を設定

## 5. AWS デプロイ

### ECS (Elastic Container Service) 使用

1. **ECR リポジトリ作成**
```bash
aws ecr create-repository --repository-name moodflix
```

2. **Docker イメージのビルド・プッシュ**
```bash
# イメージのビルド
docker build -t moodflix .

# ECRにタグ付け
docker tag moodflix:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/moodflix:latest

# プッシュ
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/moodflix:latest
```

3. **ECS タスク定義**
```json
{
  "family": "moodflix-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "moodflix",
      "image": "123456789012.dkr.ecr.us-west-2.amazonaws.com/moodflix:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789012:secret:moodflix/openai-key"
        }
      ]
    }
  ]
}
```

## 6. Cloudflare 統合

### CDN・WAF設定

1. **ドメイン設定**
   - Cloudflareでドメインを管理
   - DNS設定でアプリケーションを指定

2. **SSL/TLS設定**
   - 「Full (strict)」モードを選択
   - 自動HTTPS リダイレクト有効化

3. **WAF ルール**
```javascript
// Cloudflare Workers でのレート制限
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const ip = request.headers.get('CF-Connecting-IP')
  
  // レート制限チェック
  const rateLimitKey = `rate_limit:${ip}`
  const count = await RATE_LIMIT_KV.get(rateLimitKey)
  
  if (count && parseInt(count) > 100) {
    return new Response('Rate limit exceeded', { status: 429 })
  }
  
  // 元のリクエストを転送
  return fetch(request)
}
```

4. **キャッシュ設定**
```javascript
// Page Rules
/*moodflix.example.com/static/*
  Cache Level: Cache Everything
  Edge Cache TTL: 1 month

/*moodflix.example.com/api/*
  Cache Level: Bypass
```

## 7. 本番環境設定

### 環境変数（本番用）

```env
# 本番環境 .env
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-super-secret-production-key

# API Keys
OPENAI_API_KEY=sk-your-production-key
TMDB_API_KEY=your-production-key

# セキュリティ設定
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=3
RATE_LIMIT_PER_DAY=100
OPENAI_MONTHLY_LIMIT=50

# CORS設定
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis設定（本番）
REDIS_URL=redis://your-redis-host:6379/0

# ログ設定
LOG_LEVEL=INFO

# 監視設定
SENTRY_DSN=https://your-sentry-dsn
```

### Docker Compose（本番用）

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build: ./backend
    environment:
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

### Nginx設定（本番用）

```nginx
# nginx/nginx.conf
upstream backend {
    server backend:5000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # セキュリティヘッダー
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 静的ファイル
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # フロントエンド
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 8. 監視・運用

### ヘルスチェック設定

```bash
# ヘルスチェックスクリプト
#!/bin/bash
# health-check.sh

HEALTH_URL="https://yourdomain.com/api/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

### ログ監視

```bash
# ログローテーション設定
# /etc/logrotate.d/moodflix
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker compose restart backend
    endscript
}
```

### バックアップスクリプト

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Redis データのバックアップ
docker compose exec redis redis-cli BGSAVE
docker cp moodflix_redis_1:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 設定ファイルのバックアップ
tar -czf $BACKUP_DIR/config_$DATE.tar.gz .env docker-compose.yml nginx/

# 古いバックアップの削除（30日以上）
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

## 9. トラブルシューティング

### よくある問題

1. **Docker起動エラー**
```bash
# ポート競合の確認
sudo netstat -tulpn | grep :5000

# Docker ログの確認
docker compose logs backend
```

2. **API接続エラー**
```bash
# 環境変数の確認
docker compose exec backend env | grep API_KEY

# ネットワーク接続の確認
docker compose exec backend curl -I https://api.openai.com
```

3. **メモリ不足**
```bash
# メモリ使用量の確認
docker stats

# 不要なコンテナの削除
docker system prune -a
```

### デバッグコマンド

```bash
# コンテナ内でのデバッグ
docker compose exec backend bash

# ログレベルの変更
docker compose exec backend env LOG_LEVEL=DEBUG python app.py

# Redis接続確認
docker compose exec redis redis-cli ping
```

## 10. セキュリティチェックリスト

### デプロイ前チェック

- [ ] 環境変数に本番用の値を設定
- [ ] SECRET_KEYを強力なものに変更
- [ ] DEBUG モードを無効化
- [ ] CORS設定を本番ドメインに限定
- [ ] SSL証明書の設定
- [ ] ファイアウォール設定
- [ ] レート制限の有効化
- [ ] ログ監視の設定

### 定期チェック

- [ ] SSL証明書の有効期限
- [ ] API使用量の監視
- [ ] セキュリティアップデート
- [ ] バックアップの確認
- [ ] ログの確認

## 11. パフォーマンス最適化

### 本番環境での最適化

1. **Gunicorn設定**
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

2. **Redis最適化**
```redis
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

3. **Nginx最適化**
```nginx
worker_processes auto;
worker_connections 1024;

gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript;

client_max_body_size 10M;
client_body_timeout 12;
client_header_timeout 12;
keepalive_timeout 15;
send_timeout 10;
```

これで、MoodFlixを様々な環境に安全かつ効率的にデプロイできます。環境に応じて適切な設定を選択し、セキュリティとパフォーマンスを両立させてください。

