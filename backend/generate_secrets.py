"""Generate security keys for the application"""
import os
import secrets
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet

PROJECT_ROOT = Path(__file__).resolve().parent
SECRETS_BASE_DIR = Path(
    os.getenv(
        "MEFEED_SECRETS_DIR",
        PROJECT_ROOT.parent / "Media Feed Secrets"
    )
).resolve(strict=False)
TARGET_DIR = SECRETS_BASE_DIR / "secrets"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# Generate RSA key pair for JWT
print("Generating JWT keys...")
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Save private key
with open(TARGET_DIR / 'jwt_private.pem', 'wb') as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Save public key
with open(TARGET_DIR / 'jwt_public.pem', 'wb') as f:
    f.write(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("✓ JWT keys generated")

# Generate secret key
print("Generating secret key...")
with open(TARGET_DIR / 'secret_key.txt', 'w') as f:
    f.write(secrets.token_urlsafe(32))

print("✓ Secret key generated")

# Generate encryption key
print("Generating encryption key...")
with open(TARGET_DIR / 'encryption.key', 'wb') as f:
    f.write(Fernet.generate_key())

print("✓ Encryption key generated")
print("\nAll secrets generated successfully at", TARGET_DIR)
