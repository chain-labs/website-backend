#!/usr/bin/env python3
"""Generate a secure JWT secret key for production use."""

import secrets

def generate_jwt_secret():
    """Generate a cryptographically secure secret key."""
    secret = secrets.token_urlsafe(64)
    return secret

if __name__ == "__main__":
    secret = generate_jwt_secret()
    print("Generated JWT Secret Key:")
    print("=" * 50)
    print(secret)
    print("=" * 50)
    print("\nAdd this to your environment variables:")
    print(f"JWT_SECRET_KEY={secret}")
    print("\nFor Railway.app:")
    print("1. Go to your Railway project dashboard")
    print("2. Go to Variables section")
    print("3. Add JWT_SECRET_KEY with the value above")
    print("\nFor GitHub Actions:")
    print("1. Go to your repo → Settings → Secrets")
    print("2. Add JWT_SECRET_KEY with the value above")