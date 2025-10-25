#!/usr/bin/env python3
"""
Test database connection using configuration loader
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config_loader import config

async def test_config_db():
    try:
        print("Testing database connection using config loader...")
        
        # Get credentials from config
        import urllib.parse
        db_config = config.get_database_config()
        encoded_password = urllib.parse.quote_plus(db_config['password'])
        db_url = f"postgresql+asyncpg://{db_config['user']}:{encoded_password}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        
        print(f"Database URL: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['name']}")
        
        engine = create_async_engine(db_url)
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"SUCCESS: Connected to database!")
            print(f"PostgreSQL: {version[:80]}...")
            
            # Test basic table creation
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            await conn.commit()
            print("SUCCESS: Users table ready")
            
            return True
            
    except Exception as e:
        print(f"FAILED: {e}")
        return False
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_config_db())
