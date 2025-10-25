#!/usr/bin/env python3
"""
Simple Secret Generation for Me Feed
"""

import os
import secrets
import sys
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet

# Configuration
SECRETS_DIR = Path(__file__).parent.parent / "secrets"
JWT_KEY_SIZE = 2048

def ensure_secrets_dir():
    SECRETS_DIR.mkdir(exist_ok=True)
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR, 0o700)
    print(f"Secrets directory created: {SECRETS_DIR}")

def generate_jwt_keypair():
    print("Generating JWT RSA Keypair...")
    
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=JWT_KEY_SIZE
    )
    
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(SECRETS_DIR / "jwt_private.pem", "wb") as f:
        f.write(private_pem)
    
    with open(SECRETS_DIR / "jwt_public.pem", "wb") as f:
        f.write(public_pem)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "jwt_private.pem", 0o600)
        os.chmod(SECRETS_DIR / "jwt_public.pem", 0o644)
    
    print("JWT Keypair generated successfully")

def generate_encryption_key():
    print("Generating Fernet Encryption Key...")
    
    key = Fernet.generate_key()
    
    with open(SECRETS_DIR / "encryption.key", "wb") as f:
        f.write(key)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "encryption.key", 0o600)
    
    print("Encryption key generated successfully")

def generate_database_credentials():
    print("Generating Database Credentials...")
    
    db_user = "mefeed_user"
    db_password = secrets.token_urlsafe(32)
    
    with open(SECRETS_DIR / "db_user.txt", "w") as f:
        f.write(db_user)
    
    with open(SECRETS_DIR / "db_password.txt", "w") as f:
        f.write(db_password)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "db_user.txt", 0o640)
        os.chmod(SECRETS_DIR / "db_password.txt", 0o600)
    
    print(f"Database credentials generated (user: {db_user})")

def generate_redis_credentials():
    print("Generating Redis Credentials...")
    
    redis_password = secrets.token_urlsafe(32)
    
    with open(SECRETS_DIR / "redis_password.txt", "w") as f:
        f.write(redis_password)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "redis_password.txt", 0o600)
    
    print("Redis credentials generated")

def generate_application_secret():
    print("Generating Application Secret...")
    
    app_secret = secrets.token_urlsafe(64)
    
    with open(SECRETS_DIR / "app_secret.txt", "w") as f:
        f.write(app_secret)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "app_secret.txt", 0o600)
    
    print("Application secret generated")

def generate_api_keys():
    print("Generating API Keys...")
    
    # Email API key
    email_key = secrets.token_urlsafe(32)
    with open(SECRETS_DIR / "email_api_key.txt", "w") as f:
        f.write(email_key)
    
    # TMDB API key
    tmdb_key = secrets.token_urlsafe(32)
    with open(SECRETS_DIR / "tmdb_api_key.txt", "w") as f:
        f.write(tmdb_key)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "email_api_key.txt", 0o600)
        os.chmod(SECRETS_DIR / "tmdb_api_key.txt", 0o600)
    
    print("API keys generated successfully")

def main():
    print("ME FEED - Secret Generation System")
    print("=" * 50)
    
    try:
        ensure_secrets_dir()
        generate_application_secret()
        generate_jwt_keypair()
        generate_encryption_key()
        generate_database_credentials()
        generate_redis_credentials()
        generate_api_keys()
        
        print("\n" + "=" * 50)
        print("ALL SECRETS GENERATED SUCCESSFULLY!")
        print(f"Directory: {SECRETS_DIR}")
        print("Files created: 9 secure files")
        print("Algorithm: RSA-2048, Fernet AES-256")
        print("Ready for deployment!")
        
        return 0
        
    except Exception as e:
        print(f"\nError during secret generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
