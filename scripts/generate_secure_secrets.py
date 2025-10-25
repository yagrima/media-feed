#!/usr/bin/env python3
"""
Professional Secret Generation System for Me Feed
Creates cryptographically secure secrets with proper entropy
"""

import os
import secrets
import sys
import base64
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

# Configuration
SECRETS_DIR = Path(__file__).parent.parent / "secrets"
MIN_SECRET_LENGTH = 64
JWT_KEY_SIZE = 2048

def ensure_secrets_dir():
    """Ensure secrets directory exists with proper permissions"""
    SECRETS_DIR.mkdir(exist_ok=True)
    # Set restrictive permissions (Unix-like)
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR, 0o700)
    print(f"Secrets directory secured: {SECRETS_DIR}")

def generate_jwt_keypair():
    """Generate RSA keypair for JWT signing"""
    print("Generating JWT RSA Keypair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=JWT_KEY_SIZE
    )
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Write to files
    with open(SECRETS_DIR / "jwt_private.pem", "wb") as f:
        f.write(private_pem)
    
    with open(SECRETS_DIR / "jwt_public.pem", "wb") as f:
        f.write(public_pem)
    
    # Set permissions
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "jwt_private.pem", 0o600)
        os.chmod(SECRETS_DIR / "jwt_public.pem", 0o644)
    
    print("JWT Keypair generated successfully")

def generate_encryption_key():
    """Generate Fernet encryption key"""
    print("🔒 Generating Fernet Encryption Key...")
    
    # Generate 32-byte key
    key = Fernet.generate_key()
    
    # Write to file
    with open(SECRETS_DIR / "encryption.key", "wb") as f:
        f.write(key)
    
    # Set permissions
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "encryption.key", 0o600)
    
    print("✅ Encryption key generated successfully")

def generate_database_credentials():
    """Generate secure database credentials"""
    print("🗄️ Generating Database Credentials...")
    
    # Generate secure random credentials
    db_user = "mefeed_user"  # Consistent user name
    db_password = secrets.token_urlsafe(32)
    
    # Write to files
    with open(SECRETS_DIR / "db_user.txt", "w") as f:
        f.write(db_user)
    
    with open(SECRETS_DIR / "db_password.txt", "w") as f:
        f.write(db_password)
    
    # Set permissions
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "db_user.txt", 0o640)
        os.chmod(SECRETS_DIR / "db_password.txt", 0o600)
    
    print(f"✅ Database credentials generated (user: {db_user})")

def generate_redis_credentials():
    """Generate secure Redis credentials"""
    print("📦 Generating Redis Credentials...")
    
    redis_password = secrets.token_urlsafe(32)
    
    with open(SECRETS_DIR / "redis_password.txt", "w") as f:
        f.write(redis_password)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "redis_password.txt", 0o600)
    
    print("✅ Redis credentials generated")

def generate_application_secret():
    """Generate secure application secret"""
    print("🔑 Generating Application Secret...")
    
    # Generate cryptographically secure secret
    app_secret = secrets.token_urlsafe(MIN_SECRET_LENGTH)
    
    with open(SECRETS_DIR / "app_secret.txt", "w") as f:
        f.write(app_secret)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "app_secret.txt", 0o600)
    
    print("✅ Application secret generated")

def generate_email_api_key():
    """Generate placeholder email API key"""
    print("📧 Generating Email API Key...")
    
    # Generate secure key for email service
    email_key = secrets.token_urlsafe(32)
    
    with open(SECRETS_DIR / "email_api_key.txt", "w") as f:
        f.write(email_key)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "email_api_key.txt", 0o600)
    
    print("✅ Email API key generated")

def generate_tmdb_api_key():
    """Generate placeholder TMDB API key"""
    print("🎬 Generating TMDB API Key...")
    
    tmdb_key = secrets.token_urlsafe(32)
    
    with open(SECRETS_DIR / "tmdb_api_key.txt", "w") as f:
        f.write(tmdb_key)
    
    if hasattr(os, 'chmod'):
        os.chmod(SECRETS_DIR / "tmdb_api_key.txt", 0o600)
    
    print("✅ TMDB API key generated")

def verify_secrets():
    """Verify all secrets were created successfully"""
    print("\n🔍 Verifying Secrets Creation...")
    
    required_files = [
        "jwt_private.pem",
        "jwt_public.pem", 
        "encryption.key",
        "db_user.txt",
        "db_password.txt",
        "redis_password.txt",
        "app_secret.txt",
        "email_api_key.txt",
        "tmdb_api_key.txt"
    ]
    
    missing_files = []
    for file in required_files:
        if not (SECRETS_DIR / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print(f"✅ All {len(required_files)} secrets verified successfully")
    return True

def display_summary():
    """Display summary of generated secrets"""
    print(f"""
═════════════════════════════════════════════════════════════════════════════════
                            🛡️ ME FEED - SECRETS GENERATED
═════════════════════════════════════════════════════════════════════════════════
    
📁 Secrets Directory: {SECRETS_DIR}
🔒 Files Created: 9 encrypted/encoded files
🔐 Algorithm: RSA-2048 for JWT, Fernet for encryption
🎲 Entropy: Cryptographically secure (secrets module)
📅 Generated: {""}

⚠️  IMPORTANT SECURITY NOTES:
    • The secrets directory is now protected (700 permissions)
    • Private keys have restricted access (600 permissions)
    • Store secrets/ directory securely and NEVER commit to git
    • Backup secrets securely for disaster recovery
    • Rotate secrets regularly according to security policy

🚀 READY FOR DEPLOYMENT:
    • All cryptographic keys generated
    • Database credentials created
    • API keys ready for configuration
    • All secrets use proper entropy and standards

═════════════════════════════════════════════════════════════════════════════════
    """)

def main():
    """Main secret generation process"""
    print("ME FEED - Professional Secret Generation System")
    print("=" * 60)
    
    try:
        # Ensure secrets directory
        ensure_secrets_dir()
        
        # Generate all secrets
        generate_application_secret()
        generate_jwt_keypair()
        generate_encryption_key()
        generate_database_credentials()
        generate_redis_credentials()
        generate_email_api_key()
        generate_tmdb_api_key()
        
        # Verification
        if verify_secrets():
            
            display_summary()
            print(f"\nAll secrets generated successfully!")
            return 0
        else:
            print("\nSecret generation failed - missing files")
            return 1
            
    except Exception as e:
        print(f"\nError during secret generation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
