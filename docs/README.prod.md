# Production Deployment

## Overview

This guide covers production deployment of Reading Tracker API using Docker Compose with production-optimized configurations.

## Requirements

- Docker & Docker Compose v2+
- Domain name (optional, for HTTPS)
- SSL certificates (optional)

## Production Features

| Feature | Description |
|----------|-------------|
| **Multi-stage Build** | Smaller Docker image (~200MB vs ~800MB) |
| **Resource Limits** | CPU/memory limits on all services |
| **Restart Policies** | `unless-stopped` for reliability |
| **Secrets** | Environment-based secrets (no hardcoding) |
| **Redis Auth** | Password-protected Redis |
| **Database Scheduler** | Celery Beat with persistent schedule |
| **JSON Logging** | Structured logs for monitoring |
| **Health Checks** | Container health monitoring |

## Quick Start

### 1. Generate Secrets

```bash
# Generate secure JWT secret
openssl rand -hex 32

# Generate secure Redis password
openssl rand -hex 32

# Generate secure PostgreSQL password
openssl rand -hex 32
```

### 2. Create Production Environment

```bash
# Copy example and fill in secrets
cp .env.example .env

# Edit .env with production values:
# - JWT_SECRET_KEY=<generated-jwt-secret>
# - POSTGRES_PASSWORD=<generated-pg-password>
# - REDIS_PASSWORD=<generated-redis-password>
```

### 3. Deploy

```bash
# Build images
docker compose -f docker-compose.prod.yml build

# Start services (API + infrastructure only)
docker compose -f docker-compose.prod.yml up -d

# Or include Celery (worker + beat)
docker compose -f docker-compose.prod.yml --profile celery up -d
```

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker compose -f docker-compose.prod.yml logs -f api
```

## Services

### API (`reading_tracker_api`)
- FastAPI application
- Health check at `/health`
- Resource limits: 2 CPU, 512MB RAM
- Rate limiting enabled

### Worker (`reading_tracker_worker`)
- Celery worker for async tasks
- Handles: abandoned books, cleanup, reports
- Resource limits: 1 CPU, 512MB RAM

### Beat (`reading_tracker_beat`)
- Celery Beat scheduler
- Uses Django Celery Beat DatabaseScheduler
- Persists schedule across restarts
- Resource limits: 0.5 CPU, 256MB RAM

### PostgreSQL (`reading_tracker_postgres`)
- Database: `reading_tracker`
- Persistent volume
- Resource limits: 1 CPU, 512MB RAM

### Redis (`reading_tracker_redis`)
- Cache & Celery broker
- Password-protected
- Resource limits: 0.5 CPU, 256MB RAM

## Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| `check_abandoned_books` | Daily | Mark books inactive for 30+ days as abandoned |
| `calculate_user_streaks` | Daily | Calculate reading streaks |
| `update_leaderboard` | Hourly | Update top users cache |
| `cleanup_old_sessions` | Weekly | Delete sessions older than 365 days |

## Environment Variables

### Required Secrets

| Variable | Description |
|----------|-------------|
| `JWT_SECRET_KEY` | 64-char hex string for JWT signing |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `REDIS_PASSWORD` | Redis password |

### Optional Overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `reading_tracker` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `API_PORT` | `8000` | API port |
| `LOG_LEVEL` | `WARNING` | Logging level |
| `DATABASE_POOL_SIZE` | `10` | DB connection pool |
| `RATE_LIMIT_PER_MINUTE` | `100` | API rate limit |

### Resource Limits

| Variable | Default | Description |
|----------|---------|-------------|
| `API_CPU_LIMIT` | `2` | API CPU cores |
| `API_MEMORY_LIMIT` | `512M` | API memory |
| `WORKER_CPU_LIMIT` | `1` | Worker CPU cores |
| `WORKER_MEMORY_LIMIT` | `512M` | Worker memory |

## Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### View Logs

```bash
# API logs
docker compose -f docker-compose.prod.yml logs -f api

# Worker logs
docker compose -f docker-compose.prod.yml logs -f worker

# Beat logs
docker compose -f docker-compose.prod.yml logs -f beat

# All services
docker compose -f docker-compose.prod.yml logs -f
```

### Check Celery Tasks

```bash
# Active tasks
docker compose -f docker-compose.prod.yml exec worker celery -A app.tasks.celery_app inspect active

# Registered tasks
docker compose -f docker-compose.prod.yml exec worker celery -A app.tasks.celery_app inspect registered
```

## Backup & Restore

### Database Backup

```bash
# Create backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres reading_tracker > backup_$(date +%Y%m%d).sql

# Compressed backup
docker compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres reading_tracker | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore from backup
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres reading_tracker

# Restore from compressed
gunzip < backup.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres reading_tracker
```

## Scaling

### Scale Workers

```bash
# Scale to 3 workers
docker compose -f docker-compose.prod.yml up -d --scale worker=3
```

### Update Deployment

```bash
# Pull latest code
git pull

# Rebuild images
docker compose -f docker-compose.prod.yml build

# Restart services
docker compose -f docker-compose.prod.yml up -d
```

## Security Checklist

- [ ] Generate strong JWT secret (`openssl rand -hex 32`)
- [ ] Generate strong PostgreSQL password
- [ ] Generate strong Redis password
- [ ] Enable HTTPS/TLS (nginx/Caddy)
- [ ] Configure CORS for specific origins
- [ ] Set appropriate rate limits
- [ ] Regular database backups
- [ ] Monitor logs for suspicious activity
- [ ] Use secrets management in production (Vault, AWS Secrets Manager)
- [ ] Enable PostgreSQL SSL connections

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs <service>

# Check status
docker compose -f docker-compose.prod.yml ps
```

### Database Connection Failed

```bash
# Check PostgreSQL is healthy
docker compose -f docker-compose.prod.yml ps postgres

# Test connection
docker compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres
```

### Celery Tasks Not Running

```bash
# Check worker is running
docker compose -f docker-compose.prod.yml ps worker

# Check beat is running
docker compose -f docker-compose.prod.yml ps beat

# View worker logs
docker compose -f docker-compose.prod.yml logs worker
```
