# Me Feed - Production Deployment Guide

## 📋 Overview

This guide provides comprehensive instructions for deploying Me Feed in a production environment. The application is fully containerized and includes all necessary services for a scalable, secure deployment.

## 🔧 Architecture Overview

### Components
- **Frontend**: Next.js application (Port 3000)
- **Backend**: FastAPI Python application (Port 8000)
- **Database**: PostgreSQL with connection pooling
- **Cache**: Redis for session storage and caching
- **Processor**: Celery for background tasks
- **Email**: Brevo SMTP integration
- **Proxy**: Nginx reverse proxy (optional)

### Data Flow
```
User → Nginx → Frontend → API → [Database/Redis/Email]
                 ↓
              Background Tasks (Celery)
```

## 🚀 QUICK START DEPLOYMENT

### 📍 IMPORTANT: NO LOCAL USERS POLICY
**This application is designed for cloud deployment only. Local access is for development and testing purposes. All production users will access the application via cloud hosting.**

### Prerequisites for Cloud Deployment
1. Choose a cloud hosting provider (see options below)
2. Secrets configured in `../Media Feed Secrets/`
3. Domain name ready (recommended)
4. Production environment variables set
5. Cloud account with billing enabled

### Cloud Deployment Options

#### Option 1: Railway (Recommended for Beginners)
```bash
# 1. Sign up at railway.app
# 2. Connect GitHub repository
# 3. Deploy using existing Docker configuration
# 4. Configure environment variables in Railway dashboard
```

#### Option 2: Render (Alternative Beginner Option)
```bash
# 1. Sign up at render.com
# 2. Connect repository
# 3. Use Docker compose configuration
# 4. Configure secrets
```

#### Option 3: AWS ECS (Production-Grade)
```bash
# 1. Set up AWS account
# 2. Configure ECS cluster
# 3. Use existing production Docker configuration
# 4. Set up ALB/Gateway
```

### Quick Cloud Deployment Commands
```bash
# Build for cloud deployment
docker build -t yagrima/mefeed-backend:latest backend/
docker build -t yagrima/mefeed-frontend:latest frontend/

# Test locally before cloud deploy (testing only)
docker-compose -f docker-checks.yml up -d
docker-compose -f docker-checks.yml down
```

## 🔐 Security Configuration

### Required Secrets
All sensitive data must be stored in `../Media Feed Secrets/secrets/`:

| File | Purpose | Example |
|------|---------|---------|
| `jwt_private.pem` | JWT private key | RSA-2048 private key |
| `jwt_public.pem` | JWT public key | RSA-2048 public key |
| `encryption.key` | Data encryption | Fernet 32-byte key |
| `secret_key.txt` | Flask secret | 64+ character string |
| `db_user.txt` | Database username | `mefeed_user` |
| `db_password.txt` | Database password | Secure password |
| `redis_password.txt` | Redis password | Secure password |

### Environment Variables
Critical variables in `../Media Feed Secrets/.env.prod`:

```env
# Database (loaded from secrets)
DATABASE_URL=postgresql+asyncpg://$(cat /run/secrets/db_user):$(cat /run/secrets/db_password)@db:5432/$(cat /run/secrets/db_name)
REDIS_URL=redis://:$(cat /run/secrets/redis_password)@redis:6379

# Email Configuration
SMTP_HOST=smtp-relay.brevo.com
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
FROM_EMAIL=your_from_email

# Production URLs
ALLOWED_ORIGINS=https://mefeed.com,https://www.mefeed.com
ALLOWED_HOSTS=mefeed.com,www.mefeed.com

# Security Settings
DEBUG=false
ENFORCE_HTTPS=true
```

## 📊 Monitoring & Logging

### Health Endpoints
- **System Health**: `GET /health`
- **Database Health**: Included in health check
- **Application Metrics**: `GET /metrics` (if enabled)

### Logging Configuration
```json
{
  "level": "INFO",
  "format": "json",
  "structured": true,
  "requests": true,
  "performance": true,
  "security_events": true
}
```

### Monitoring Commands
```bash
# View service health
docker-compose -f docker-checks.yml ps

# View logs in real-time
docker-compose -f docker-checks.yml logs -f backend

# Check resource usage
docker stats

# Access logs
docker exec mefeed_backend_prod curl -s http://localhost:8000/health
```

## 🛠️ Configuration Management

### Production Configuration Files
- `docker-checks.yml` - Full production stack with health checks
- `nginx/nginx.prod.conf` - Nginx reverse proxy configuration
- `config/production.env` - Production-optimized environment settings

### Environment Profiles
| Environment | File | Debug | HTTPS | Rate Limiting |
|-------------|------|-------|-------|---------------|
| Development | `.env` | true | false | Relaxed |
| Production | `.env.prod` | false | true | Strict |

## 📈 Performance Optimization

### Database Optimization
```env
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=3600
DATABASE_POOL_PRE_PING=true
```

### Caching Strategy
- **Session Storage**: Redis with TTL
- **API Response**: 5 minute default TTL
- **Static Assets**: 1 year cache
- **Database Queries**: Connection pooling

### Resource Limits
```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '0.5'
    reservations:
      memory: 256M
      cpus: '0.25'
```

## 🔧 Advanced Configuration

### SSL/HTTPS Setup
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### Rate Limiting
```nginx
# API endpoints
limir_req zone=api_limit burst=10 nodelay;

# Authentication endpoints 
limit_req zone=auth_limit burst=5 nodelay;

# Upload endpoints
limir_req zone=upload_limit burst=3 nodelay;
```

### Backup Strategy
```bash
# Database backup
docker exec mefeed_db_prod_check pg_dump -U mefeed_user mefeed > backup.sql

# Volume backup
docker run --rm -v mefeed_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz -C /data .
```

## 🧪 Testing & Validation

### Production Readiness Tests
```bash
# Run full test suite
python tests/integration/test_production_readiness.py

# Individual test categories
pytest tests/integration/test_production_readiness.py::TestAuthenticationFlow
pytest tests/integration/test_production_readiness.py::TestEmailFunctionality
pytest tests/integration/test_production_readiness.py::TestDatabaseAndAPI
```

### Manual Testing Checklist
- [ ] User registration and email verification
- [ ] Password reset flow
- [ ] CSV import functionality
- [ ] Media library browsing
- [ ] Notification preferences
- [ ] Frontend responsiveness (mobile/desktop)
- [ ] API authentication and security
- [ ] File upload size limits
- [ ] Error handling and user feedback

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Database Connection Issues
```bash
# Check database health
docker exec mefeed_db_prod_check pg_isready -U mefeed_user

# Check database logs
docker-compose -f docker-checks.yml logs db

# Restart database
docker-compose -f docker-checks.yml restart db
```

#### Email Issues
```bash
# Test SMTP connection
python scripts/test_email.py

# Check SMTP settings
docker exec mefeed_backend_prod python -c "from app.core.config import Settings; print(Settings().SMTP_HOST)"

# Verify email logs
docker-compose -f docker-checks.yml logs backend | grep -i email
```

#### Frontend Issues
```bash
# Check frontend build
docker-compose -f docker-checks.yml logs frontend

# Rebuild frontend
docker-compose -f docker-checks.yml up -d --build frontend

# Check network connectivity
docker-compose -f docker-checks.yml exec frontend curl -f http://localhost:3000
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Monitor database queries
docker exec mefeed_db_prod_check psql -U mefeed_user -d mefeed -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check Redis memory
docker exec mefeed_redis_prod_check redis-cli info memory
```

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh
- `POST /api/auth/verify-email` - Email verification
- `POST /api/auth/reset-password` - Password reset

### Media Management
- `GET /api/media` - List media
- `POST /api/media/import` - Import CSV
- `GET /api/media/export` - Export data
- `DELETE /api/media/{id}` - Delete media

### Notifications
- `GET /api/notifications` - List notifications
- `PUT /api/notifications/{id}/read` - Mark as read
- `POST /api/notifications/unsubscribe` - Unsubscribe

Full API documentation available at: `http://localhost:8000/docs`

## 🔄 Maintenance Procedures

### Daily Tasks
- [ ] Check application health status
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backups successful

### Weekly Tasks
- [ ] Update security patches
- [ ] Review performance metrics
- [ ] Cleanup old logs
- [ ] Verify SSL certificates

### Monthly Tasks
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Backup verification
- [ ] Dependency updates

## 📞 Support

For production issues:

1. **Immediate Response**: Check health endpoints and logs
2. **User Impact**: Activate maintenance mode if needed
3. **Technical Support**: Contact system administrator
4. **The Frontend**: Provide user communication

### Emergency Contacts
- **System Administrator**: [Contact Information]
- **DevOps Team**: [Contact Information]
- **Security Team**: [Contact Information]

---

## 📝 Version History

- **v1.1.0** - Production-ready with full email integration
- **v1.0.0** - Initial MVP release

---

**Last Updated**: October 26, 2025  
**Maintainer**: Me Feed Development Team
