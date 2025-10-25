# Docker Setup & Integration Testing

**Date**: October 20, 2025
**Status**: Ready for Docker-based testing

---

## Prerequisites

1. **Docker Desktop**: Must be running
2. **Secrets**: Already generated in `./secrets/`
3. **Environment**: `.env` file configured

---

## Quick Start

```bash
# Navigate to project root
cd "G:\My Drive\KI-Dev\Me(dia) Feed"

# Build all services
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Access applications
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Backend API docs: http://localhost:8000/docs
```

---

## Step-by-Step Setup

### 1. Start Docker Desktop

**Windows**:
- Open Docker Desktop application
- Wait for "Docker Desktop is running" status
- Check system tray icon is green

**Verify**:
```bash
docker --version
# Should show: Docker version 28.5.1+

docker ps
# Should show empty list (no error)
```

---

### 2. Build Services

```bash
cd "G:\My Drive\KI-Dev\Me(dia) Feed"

# Build all services (first time ~10-15 minutes)
docker-compose build

# Or build specific service
docker-compose build frontend
docker-compose build backend
```

**Expected output**:
```
[+] Building frontend...
[+] Building backend...
Successfully built <image-id>
```

---

### 3. Start Services

```bash
# Start all services in background
docker-compose up -d

# Or start with logs visible
docker-compose up
```

**Services started**:
- `mefeed_db` - PostgreSQL database
- `mefeed_redis` - Redis cache
- `mefeed_backend` - FastAPI backend
- `mefeed_celery` - Celery worker (if configured)
- `mefeed_frontend` - Next.js frontend

---

### 4. Verify Services

```bash
# Check all services running
docker-compose ps

# Should show all services as "Up (healthy)"
```

**Health checks**:
```bash
# Database
docker exec mefeed_db pg_isready

# Redis
docker exec mefeed_redis redis-cli ping

# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

---

### 5. Run Database Migrations

```bash
# Run migrations (first time only)
docker exec mefeed_backend alembic upgrade head

# Verify migrations
docker exec mefeed_backend alembic current
```

---

## Service Details

### Frontend (Port 3000)

**Container**: `mefeed_frontend`
**Image**: Built from `./frontend/Dockerfile`
**Access**: http://localhost:3000

**Environment**:
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `NODE_ENV=production`

**Logs**:
```bash
docker logs mefeed_frontend -f
```

---

### Backend (Port 8000)

**Container**: `mefeed_backend`
**Image**: Built from `./backend/Dockerfile`
**Access**: http://localhost:8000

**API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

**Logs**:
```bash
docker logs mefeed_backend -f
```

---

### Database (PostgreSQL)

**Container**: `mefeed_db`
**Port**: 5432 (internal)
**Database**: `mefeed`
**User**: From `./secrets/db_user.txt`
**Password**: From `./secrets/db_password.txt`

**Connect**:
```bash
docker exec -it mefeed_db psql -U mefeed_user -d mefeed
```

---

### Redis (Cache)

**Container**: `mefeed_redis`
**Port**: 6379 (internal)
**Password**: From `./secrets/redis_password.txt`

**Connect**:
```bash
docker exec -it mefeed_redis redis-cli
AUTH <password>
```

---

## Testing Workflow

### 1. Create Test User

```bash
# Via backend API
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

**Or via database**:
```bash
docker exec -it mefeed_db psql -U mefeed_user -d mefeed

-- Check users
SELECT id, email, created_at FROM users;
```

---

### 2. Test Frontend

```bash
# Open browser
open http://localhost:3000

# Or use curl
curl -I http://localhost:3000
```

**Test flow**:
1. Navigate to http://localhost:3000/login
2. Login with test user
3. Check navbar for notifications
4. Navigate to http://localhost:3000/dashboard/notifications

---

### 3. Create Test Notifications

```bash
# Via database
docker exec -it mefeed_db psql -U mefeed_user -d mefeed

-- Get user ID
SELECT id FROM users WHERE email = 'test@example.com';

-- Insert test notifications
INSERT INTO notifications (user_id, type, title, message, data, read)
VALUES
  ('<user-id>', 'sequel_detected', 'New Sequel Available',
   'Stranger Things Season 5 is now available',
   '{"media_title": "Stranger Things S4", "sequel_title": "Stranger Things S5"}'::jsonb,
   false),
  ('<user-id>', 'import_complete', 'Import Complete',
   'Your CSV import finished successfully',
   '{"total_rows": 100}'::jsonb,
   false);

-- Verify
SELECT id, type, title, read FROM notifications;
```

---

### 4. Run Integration Tests

Follow `INTEGRATION_TEST_PLAN.md` tests 1-15:

```bash
# Test 1: Authentication
# Login at http://localhost:3000/login

# Test 2: Notification badge
# Refresh page, check navbar badge shows "2"

# Test 3: Notification center
# Click Notifications, verify list displays

# ... continue through all 15 tests
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Common issues:
# - Port already in use
# - Secrets file missing
# - Database migration needed
```

### Port Conflicts

If port 3000 or 8000 already in use:

```bash
# Find process using port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill process (PowerShell as Admin)
taskkill /PID <pid> /F

# Or change ports in docker-compose.yml
```

### Database Connection Issues

```bash
# Check database logs
docker logs mefeed_db

# Verify secrets
cat secrets/db_user.txt
cat secrets/db_password.txt

# Test connection
docker exec mefeed_backend python -c "from app.core.database import engine; engine.connect()"
```

### Frontend Build Fails

```bash
# Check build logs
docker-compose logs frontend

# Common fixes:
# - Clear Docker cache: docker-compose build --no-cache frontend
# - Check Dockerfile syntax
# - Verify next.config.js has output: 'standalone'
```

### Redis Connection Issues

```bash
# Check Redis logs
docker logs mefeed_redis

# Test connection
docker exec mefeed_redis redis-cli ping

# Should return: PONG
```

---

## Useful Commands

### Container Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (DANGER: deletes data)
docker-compose down -v

# Restart single service
docker-compose restart frontend

# Rebuild and restart
docker-compose up -d --build frontend
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 frontend

# Since specific time
docker-compose logs --since 2025-10-20T10:00:00
```

### Exec Commands

```bash
# Backend shell
docker exec -it mefeed_backend sh

# Run Python script
docker exec mefeed_backend python -c "print('hello')"

# Database query
docker exec -it mefeed_db psql -U mefeed_user -d mefeed -c "SELECT COUNT(*) FROM users;"

# Redis command
docker exec mefeed_redis redis-cli KEYS '*'
```

### Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove all unused images
docker image prune -a

# Remove all unused volumes
docker volume prune

# Nuclear option (removes everything)
docker system prune -a --volumes
```

---

## Development Workflow

### Code Changes

**Frontend**:
```bash
# Make changes to frontend code
# Rebuild and restart
docker-compose build frontend
docker-compose up -d frontend
```

**Backend**:
```bash
# Make changes to backend code
# Restart backend (volume mounted as :ro)
docker-compose restart backend

# Or rebuild if dependencies changed
docker-compose build backend
docker-compose up -d backend
```

### Database Changes

```bash
# Create migration
docker exec mefeed_backend alembic revision --autogenerate -m "description"

# Apply migration
docker exec mefeed_backend alembic upgrade head

# Rollback
docker exec mefeed_backend alembic downgrade -1
```

---

## Environment Variables

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)

Already configured with:
- Database URL
- Redis URL
- Secret keys
- CORS origins
- Email config

---

## Performance Notes

**Build times**:
- First build: 10-15 minutes
- Subsequent builds: 2-5 minutes (with cache)
- Frontend rebuild: 3-5 minutes
- Backend rebuild: 1-2 minutes

**Resource usage**:
- RAM: ~2GB total
- Disk: ~1.5GB images
- CPU: Low (idle), High (during build)

---

## Production Deployment

**NOT production-ready**. Current setup is for development/testing.

**Required for production**:
- [ ] Change all default passwords
- [ ] Generate new secret keys
- [ ] Configure real SMTP server
- [ ] Set DEBUG=false
- [ ] Add reverse proxy (nginx)
- [ ] Configure SSL/TLS
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Review security settings

---

## Next Steps

1. Start Docker Desktop
2. Run `docker-compose build`
3. Run `docker-compose up -d`
4. Create test user
5. Follow `INTEGRATION_TEST_PLAN.md`
6. Document results

**Access URLs**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
