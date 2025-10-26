import asyncio
import asyncpg
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user=os.getenv('DB_USER', 'mefeed_user'),
            password=os.getenv('DB_PASSWORD'),
            database='mefeed',
            host='127.0.0.1',
            port=5432
        )
        print('✅ asyncpg connection SUCCESS!')
        version = await conn.fetchval('SELECT version()')
        print(f'PostgreSQL version: {version}')
        await conn.close()
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_connection())
