-- Database Setup Script for Me Feed
-- Run as postgres superuser

-- 1. Drop existing user and database if they exist
DROP DATABASE IF EXISTS mefeed;
DROP USER IF EXISTS mefeed_admin;
DROP USER IF EXISTS mefeed_user;

-- 2. Create new user with password from external secrets
-- Password location: ../Media Feed Secrets/secrets/db_password.txt
CREATE USER mefeed_admin WITH PASSWORD 'PASSWORD_FROM_SECRETS_DIR';

-- 3. Create database with the new user as owner
CREATE DATABASE mefeed OWNER mefeed_admin;

-- 4. Grant privileges
GRANT ALL PRIVILEGES ON DATABASE mefeed TO mefeed_admin;

-- 5. Connect to the new database and set up schema permissions
\c mefeed

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO mefeed_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mefeed_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mefeed_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mefeed_admin;

-- 6. Test the connection
\c mefeed mefeed_admin
SELECT current_database(), current_user, version() as postgresql_version;

-- 7. Show connection info
\l
\du
