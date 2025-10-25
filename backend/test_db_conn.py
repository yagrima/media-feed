import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user='mefeed_user',
            password='mefeed_pass_2024',
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
