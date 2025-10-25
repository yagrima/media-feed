#!/usr/bin/env python3
"""
Database setup script using asyncpg
"""
import asyncio
import asyncpg

async def setup_database():
    """Create database and user"""
    
    # Connect as postgres superuser (try common default passwords)
    passwords = ['postgres', '', 'admin', 'password']
    conn = None
    
    for password in passwords:
        try:
            print(f"Trying to connect as postgres with password: {repr(password)}")
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='postgres',
                password=password,
                database='postgres'
            )
            print("✓ Connected to PostgreSQL as postgres")
            break
        except Exception as e:
            print(f"Failed with password {repr(password)}: {e}")
            continue
    
    if not conn:
        print("✗ Could not connect as postgres superuser")
        print("Please ensure PostgreSQL is running and postgres user has password protection disabled")
        return False
    
    try:
        # Create user
        print("Creating mefeed_admin user...")
        await conn.execute('''
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog pg_roles WHERE rolname = 'mefeed_admin') THEN
                    CREATE USER mefeed_admin WITH PASSWORD 'MFdb@2024!Secure';
                END IF;
            END
            $$;
        ''')
        print("✓ User created")
        
        # Create database
        print("Creating mefeed database...")
        await conn.execute('''
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mefeed') THEN
                    CREATE DATABASE mefeed OWNER mefeed_admin;
                END IF;
            END
            $$;
        ''')
        print("✓ Database created")
        
        # Grant privileges
        print("Setting up privileges...")
        await conn.execute('GRANT ALL PRIVILEGES ON DATABASE mefeed TO mefeed_admin;')
        print("✓ Privileges granted")
        
        # Connect to new database as new user to set up schema permissions
        await conn.close()
        
        try:
            print("Connecting to mefeed database as mefeed_admin...")
            conn2 = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='mefeed_admin',
                password='MFdb@2024!Secure',
                database='mefeed'
            )
            print("✓ Connected as mefeed_admin")
            
            # Test basic query
            result = await conn2.fetchval('SELECT current_database()')
            print(f"✓ Current database: {result}")
            
            await conn2.close()
            
        except Exception as e:
            print(f"✗ Failed to connect as mefeed_admin: {e}")
            return False
            
        print("✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False
    finally:
        if conn:
            await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_database())
