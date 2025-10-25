"""Generate security keys for the application"""
import os
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet

# Create secrets directory if it doesn't exist
os.makedirs('secrets', exist_ok=True)

# Generate RSA key pair for JWT
print("Generating JWT keys...")
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

# Save private key
with open('secrets/jwt_private.pem', 'wb') as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Save public key
with open('secrets/jwt_public.pem', 'wb') as f:
    f.write(key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

print("✓ JWT keys generated")

# Generate secret key
print("Generating secret key...")
with open('secrets/secret_key.txt', 'w') as f:
    f.write(secrets.token_urlsafe(32))

print("✓ Secret key generated")

# Generate encryption key
print("Generating encryption key...")
with open('secrets/encryption.key', 'wb') as f:
    f.write(Fernet.generate_key())

print("✓ Encryption key generated")
print("\nAll secrets generated successfully!")
