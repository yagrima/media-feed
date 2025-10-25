#!/usr/bin/env python3
"""
Simple database connection test
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_db_connection():
    # Set environment variables
    os.environ['DATABASE_URL'] = "postgresql+asyncpg://mefeed_admin:MFdb@2024!Secure@localhost:5432/mefeed"
    
    try:
        print("Testing database connection...")
        engine = create_async_engine(os.environ['DATABASE_URL'])
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Database connected successfully!")
            print(f"PostgreSQL version: {version[:50]}...")
            
            # Check if mefeed database exists
            result = await conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✓ Connected to database: {db_name}")
            
            # Create users table if it doesn't exist
            print("Creating users table if needed...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email_verified BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    last_login_at TIMESTAMP WITH TIME ZONE
                )
            """))
            await conn.commit()
            print("✓ Users table ready")
            
            # Check existing users
            result = await conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"✓ Current users in database: {count}")
            
            return True
            
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    finally:
        if 'engine' in locals():
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_db_connection())
