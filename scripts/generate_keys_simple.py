#!/usr/bin/env python3
"""
Security Key Generation Script for Me Feed (Simple Version)
Generates RSA keypair for JWT and Fernet key for encryption using pure Python
"""

import os
import secrets
from pathlib import Path


def generate_rsa_keypair_openssl():
    """Generate RSA keypair using OpenSSL command if available"""
    import subprocess

    secrets_dir = Path(__file__).parent.parent / "secrets"
    secrets_dir.mkdir(exist_ok=True)
    os.chmod(secrets_dir, 0o700)

    try:
        # Generate private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", str(secrets_dir / "jwt_private.pem"),
            "2048"
        ], check=True, capture_output=True)

        # Generate public key from private key
        subprocess.run([
            "openssl", "rsa",
            "-in", str(secrets_dir / "jwt_private.pem"),
            "-pubout",
            "-out", str(secrets_dir / "jwt_public.pem")
        ], check=True, capture_output=True)

        # Set permissions
        os.chmod(secrets_dir / "jwt_private.pem", 0o600)
        os.chmod(secrets_dir / "jwt_public.pem", 0o644)

        print("[OK] RSA keypair generated using OpenSSL")
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def generate_fernet_key():
    """Generate Fernet-compatible encryption key"""
    import base64

    secrets_dir = Path(__file__).parent.parent / "secrets"

    # Generate 32 bytes of random data and base64 encode (Fernet format)
    key = base64.urlsafe_b64encode(secrets.token_bytes(32))

    key_path = secrets_dir / "encryption.key"
    with open(key_path, 'wb') as f:
        f.write(key)
    os.chmod(key_path, 0o600)

    print("[OK] Encryption key generated")


def generate_secret_key():
    """Generate secret key for sessions"""
    secrets_dir = Path(__file__).parent.parent / "secrets"

    secret_key = secrets.token_urlsafe(64)
    secret_path = secrets_dir / "secret_key.txt"

    with open(secret_path, 'w') as f:
        f.write(secret_key)
    os.chmod(secret_path, 0o600)

    print("[OK] Secret key generated")
    print(f"  Add to .env: SECRET_KEY={secret_key}")
    return secret_key


def generate_db_credentials():
    """Generate database credentials"""
    secrets_dir = Path(__file__).parent.parent / "secrets"

    db_user = "mefeed_user"
    db_password = secrets.token_urlsafe(32)

    with open(secrets_dir / "db_user.txt", 'w') as f:
        f.write(db_user)
    with open(secrets_dir / "db_password.txt", 'w') as f:
        f.write(db_password)

    os.chmod(secrets_dir / "db_user.txt", 0o600)
    os.chmod(secrets_dir / "db_password.txt", 0o600)

    print("[OK] Database credentials generated")


def generate_redis_password():
    """Generate Redis password"""
    secrets_dir = Path(__file__).parent.parent / "secrets"

    redis_password = secrets.token_urlsafe(32)

    with open(secrets_dir / "redis_password.txt", 'w') as f:
        f.write(redis_password)
    os.chmod(secrets_dir / "redis_password.txt", 0o600)

    print("[OK] Redis password generated")


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent
    secrets_dir = project_root / "secrets"

    # Create secrets directory
    secrets_dir.mkdir(exist_ok=True)
    os.chmod(secrets_dir, 0o700)

    print("=" * 60)
    print("Me Feed Security Keys Generation (Simple)")
    print("=" * 60)
    print()

    # Try to generate RSA keypair with OpenSSL
    print("[1/5] Generating RSA keypair...")
    if not generate_rsa_keypair_openssl():
        print()
        print("⚠ OpenSSL not found or failed.")
        print("  Manual steps:")
        print("  1. Install cryptography: pip install cryptography")
        print("  2. Run: python scripts/generate_keys.py")
        print()
        print("  OR install OpenSSL:")
        print("  - Windows: https://slproweb.com/products/Win32OpenSSL.html")
        print("  - Linux: sudo apt-get install openssl")
        print("  - Mac: brew install openssl")
        print()
        return

    print()
    print("[2/5] Generating encryption key...")
    generate_fernet_key()

    print()
    print("[3/5] Generating secret key...")
    secret_key = generate_secret_key()

    print()
    print("[4/5] Generating database credentials...")
    generate_db_credentials()

    print()
    print("[5/5] Generating Redis password...")
    generate_redis_password()

    print()
    print("=" * 60)
    print("[SUCCESS] All security keys generated successfully!")
    print("=" * 60)
    print()
    print("IMPORTANT:")
    print("1. Keep the secrets/ directory secure and never commit to Git")
    print("2. Update your .env file with the SECRET_KEY shown above")
    print("3. In production, use a proper secrets management system")
    print("4. Rotate keys regularly according to your security policy")
    print("=" * 60)


if __name__ == "__main__":
    main()
