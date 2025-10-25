#!/usr/bin/env python3
"""
Security Key Generation Script for Me Feed
Generates RSA keypair for JWT and Fernet key for encryption
"""

import os
import sys
import secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet


def set_file_permissions(file_path: Path, mode: int):
    """Set file permissions (cross-platform)"""
    if sys.platform == 'win32':
        # Windows: Use icacls to restrict access
        import subprocess
        try:
            # Remove inheritance and grant only current user access
            subprocess.run([
                'icacls', str(file_path), '/inheritance:r',
                '/grant:r', f'{os.getenv("USERNAME")}:F'
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print(f"  ⚠ Warning: Could not set Windows permissions on {file_path.name}")
    else:
        # Unix-like: Use chmod
        os.chmod(file_path, mode)


def generate_jwt_keypair(secrets_dir: Path):
    """Generate RSA keypair for JWT signing"""
    print("Generating RSA keypair for JWT...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    private_key_path = secrets_dir / "jwt_private.pem"
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    set_file_permissions(private_key_path, 0o600)
    print(f"✓ Private key saved to {private_key_path}")

    # Save public key
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    public_key_path = secrets_dir / "jwt_public.pem"
    with open(public_key_path, 'wb') as f:
        f.write(public_pem)
    set_file_permissions(public_key_path, 0o644)
    print(f"✓ Public key saved to {public_key_path}")


def generate_encryption_key(secrets_dir: Path):
    """Generate Fernet encryption key"""
    print("\nGenerating Fernet encryption key...")

    key = Fernet.generate_key()
    key_path = secrets_dir / "encryption.key"

    with open(key_path, 'wb') as f:
        f.write(key)
    set_file_permissions(key_path, 0o600)
    print(f"✓ Encryption key saved to {key_path}")


def generate_secret_key(secrets_dir: Path):
    """Generate random secret key for sessions"""
    print("\nGenerating secret key...")

    secret_key = secrets.token_urlsafe(64)
    secret_path = secrets_dir / "secret_key.txt"

    with open(secret_path, 'w') as f:
        f.write(secret_key)
    set_file_permissions(secret_path, 0o600)
    print(f"✓ Secret key saved to {secret_path}")
    print(f"  Add this to your .env: SECRET_KEY={secret_key}")


def generate_db_credentials(secrets_dir: Path):
    """Generate database credentials"""
    print("\nGenerating database credentials...")

    db_user = "mefeed_user"
    db_password = secrets.token_urlsafe(32)

    with open(secrets_dir / "db_user.txt", 'w') as f:
        f.write(db_user)

    with open(secrets_dir / "db_password.txt", 'w') as f:
        f.write(db_password)

    set_file_permissions(secrets_dir / "db_user.txt", 0o600)
    set_file_permissions(secrets_dir / "db_password.txt", 0o600)

    print(f"✓ Database credentials saved")
    print(f"  User: {db_user}")
    print(f"  Password saved to secrets/db_password.txt")


def generate_redis_password(secrets_dir: Path):
    """Generate Redis password"""
    print("\nGenerating Redis password...")

    redis_password = secrets.token_urlsafe(32)

    with open(secrets_dir / "redis_password.txt", 'w') as f:
        f.write(redis_password)

    set_file_permissions(secrets_dir / "redis_password.txt", 0o600)
    print(f"✓ Redis password saved to secrets/redis_password.txt")


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent
    secrets_dir = project_root / "secrets"

    # Create secrets directory
    secrets_dir.mkdir(exist_ok=True)
    set_file_permissions(secrets_dir, 0o700)

    print("=" * 60)
    print("Me Feed Security Keys Generation")
    print("=" * 60)

    # Generate all keys
    generate_jwt_keypair(secrets_dir)
    generate_encryption_key(secrets_dir)
    generate_secret_key(secrets_dir)
    generate_db_credentials(secrets_dir)
    generate_redis_password(secrets_dir)

    print("\n" + "=" * 60)
    print("✓ All security keys generated successfully!")
    print("=" * 60)
    print("\nIMPORTANT:")
    print("1. Keep the secrets/ directory secure and never commit to Git")
    print("2. Update your .env file with the generated SECRET_KEY")
    print("3. In production, use a proper secrets management system")
    print("4. Rotate keys regularly according to your security policy")
    if sys.platform == 'win32':
        print("5. On Windows, verify file permissions with: icacls secrets\\*")
    print("=" * 60)


if __name__ == "__main__":
    main()
