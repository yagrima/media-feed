#!/usr/bin/env python3
"""
Clear users table in Railway database
"""
import os
import sys
import asyncio

# Check for DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg not installed")
    sys.exit(1)

# Ensure it's the asyncpg format
if 'postgresql+asyncpg://' in database_url:
    database_url = database_url.replace('postgresql+asyncpg://', 'postgresql://')

async def clear_users():
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Truncate users table (CASCADE will delete related data)
        print("Truncating users table...")
        await conn.execute("TRUNCATE TABLE users CASCADE;")
        
        print("[OK] All users and related data deleted successfully!")
        
        # Close connection
        await conn.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

# Run async function
asyncio.run(clear_users())
