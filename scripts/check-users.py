import asyncio
import asyncpg
import os

async def check():
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    result = await conn.fetchval('SELECT COUNT(*) FROM users')
    print(f"Users in database: {result}")
    await conn.close()

asyncio.run(check())
