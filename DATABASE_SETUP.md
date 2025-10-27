# Database Setup - Me Feed

## 📋 New Credentials

### PostgreSQL Database
- **Server**: localhost:5432
- **Database Name**: mefeed
- **User**: mefeed_admin
- **Password**: Stored in `../Media Feed Secrets/secrets/db_password.txt`
- **Superuser**: postgres (system admin)

### Redis Cache
- **Server**: localhost:6379
- **Password**: None (development setup)
- **Database**: 0

## 🚀 Setup Instructions

### 1. PostgreSQL Setup (Windows)

```sql
-- Connect as postgres superuser
-- Open PostgreSQL Command Line or pgAdmin

-- Create user
CREATE USER mefeed_admin WITH PASSWORD 'PASSWORD_FROM_SECRETS_DIR';  -- See ../Media Feed Secrets/secrets/db_password.txt

-- Create database
CREATE DATABASE mefed OWNER mefeed_admin;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mefed TO mefeed_admin;

-- Connect to mefed database and grant schema privileges
\c mefed

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO mefeed_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mefeed_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mefeed_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mefeed_admin;

-- Test connection
\c mefed mefeed_admin
SELECT current_database(), current_user;
```

### 2. Configuration Files

#### Backend Configuration (external secrets)
All configuration is now stored in `../Media Feed Secrets/` directory:
- `secrets/db_password.txt` - Database password
- `secrets/redis_password.txt` - Redis password
- `.env` - Environment variables
- `config/secrets.json` - Full configuration JSON
  "redis": {
    "password": "",
    "host": "localhost",
    "port": "6379",
    "db": "0"
  }
}
```

#### Environment Variables (fallback)
```env
DATABASE_URL=postgresql+asyncpg://mefeed_admin:MFdb@2024!Secure@localhost:5432/mefeed
REDIS_URL=redis://localhost:6379/0
```

### 3. Connection Test

```python
# Test script
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_connection():
    engine = create_async_engine(
        "postgresql+asyncpg://mefeed_admin:MFdb@2024!Secure@localhost:5432/mefeed"
    )
    
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT CURRENT_DATABASE(), CURRENT_USER"))
        db, user = result.fetchone()
        print(f"✓ Connected to {db} as {user}")

asyncio.run(test_connection())
```

## 🔧 Redis Setup (Development)

### Docker Method (Recommended)
```powershell
# Start Redis container
docker run -d --name mefeed_redis_dev -p 6379:6379 redis:7-alpine

# Test connection
docker exec -it mefeed_redis_dev redis-cli ping
```

### WSL Method (Alternative)
```bash
# In WSL terminal
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server
redis-cli ping  # Should return PONG
```

### Windows Native (Alternative)
```powershell
# Install Memurai (Redis for Windows)
# Download from https://www.memurai.com/
# Start Memurai service
```

## 📊 Database Tables (Auto-created by Alembic)

The application will automatically create these tables on startup:

### Core Tables
- `users` - User accounts and authentication
- `user_sessions` - Active user sessions
- `security_events` - Security audit log
- `media_items` - Media content tracking
- `imports` - Import job tracking
- `notifications` - User notifications

### Migration Management
```bash
# Initialize database (run once)
cd backend
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"

# Update database
alembic upgrade head
```

## 🔒 Security Notes

### Production Considerations
1. **Change passwords** before deploying to production
2. **Use SSL** for database connections in production
3. **Enable Redis authentication** in production
4. **Restrict network access** to database ports
5. **Regular backups** set up for database

### Password Security
- All passwords are stored securely using Argon2 hashing
- JWT keys use RSA-256 with 2048-bit keys
- Database connections use TLS in production

## 🚨 Troubleshooting

### Connection Issues
```bash
# Check PostgreSQL service
Get-Service postgresql*

# Manually start if needed
Start-Service postgresql-x64-18

# Test connection with psql
# Password from: ../Media Feed Secrets/secrets/db_password.txt
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U mefeed_admin -d mefed -h localhost -W
```

### Common Errors
1. **"Password authentication failed"** → Check user exists with correct password
2. **"Database does not exist"** → Create database with correct owner
3. **"Permission denied"** → Grant schema privileges to user
4. **Redis timeout** → Ensure Redis service is running

## 📝 Maintenance

### Regular Tasks
- **Weekly**: Check database size and performance
- **Monthly**: Review security event logs
- **Quarterly**: Update passwords and rotate keys
- **Yearly**: Database maintenance and optimization

### Backup Strategy
```bash
# Daily backup
pg_dump -U mefeed_admin -h localhost mefed > backup_$(date +%Y%m%d).sql

# Restore
psql -U mefeed_admin -h localhost mefed < backup_20241022.sql
```

---

## 🎯 Quick Verification

After setup, verify everything works:

1. **Database Connection**: ✐ Application starts without database errors
2. **User Registration**: ✐ Can create new users via API
3. **Authentication**: ✐ Login works with created users
4. **Redis Cache**: ✐ Sessions stored and retrieved correctly
5. **Health Check**: ✐ All health endpoints return 200 OK

**Last Updated**: 2025-10-22
**Status**: Ready for development
