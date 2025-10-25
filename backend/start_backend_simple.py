#!/usr/bin/env python3
"""
Simple backend startup script
"""
import os
import sys
import json
import urllib.parse

# Set environment variables from config
config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "secrets.json")

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Set database URL
    db_config = config.get('database', {})
    if db_config:
        encoded_password = urllib.parse.quote_plus(db_config.get('password', ''))
        db_url = f"postgresql+asyncpg://{db_config.get('user', '')}:{encoded_password}@{db_config.get('host', '')}:{db_config.get('port', '')}/{db_config.get('name', '')}"
        os.environ['DATABASE_URL'] = db_url
        print(f"Database URL configured")
    
    # Set Redis URL (skip for now)
    redis_config = config.get('redis', {})
    if redis_config:
        redis_url = "redis://localhost:6379/0"
        os.environ['REDIS_URL'] = redis_url
        print(f"Redis URL configured (skipping password)")
    
    # Set SECRET_KEY
    security_config = config.get('security', {})
    if security_config.get('secret_key'):
        os.environ['SECRET_KEY'] = security_config['secret_key']
        print(f"Secret key configured")

# Set development defaults
os.environ.setdefault('DEBUG', 'true')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')

print("Starting backend server...")
print(f"Database URL: {os.environ.get('DATABASE_URL', 'Not set')}")
print(f"Redis URL: {os.environ.get('REDIS_URL', 'Not set')}")
print(f"DEBUG mode: {os.environ.get('DEBUG', 'false')}")

# Start uvicorn
import uvicorn
if __name__ == '__main__':
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
