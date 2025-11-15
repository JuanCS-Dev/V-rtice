#!/usr/bin/env python3
"""Generate cryptographically secure JWT secret keys.

This utility helps developers and operators generate secure secret keys
for the Maximus Authentication Service, following security best practices.

Usage:
    python generate_secret_key.py [--length 32] [--env] [--check]

Examples:
    # Generate a secure key (default 32 bytes = 64 hex chars)
    python generate_secret_key.py

    # Generate key and show .env format
    python generate_secret_key.py --env

    # Check if current environment key is secure
    python generate_secret_key.py --check

    # Generate longer key (64 bytes = 128 hex chars)
    python generate_secret_key.py --length 64

Following Boris Cherny's principle: "Security is not optional"
"""

import argparse
import os
import secrets
import sys
from typing import Optional


def generate_key(length: int = 32) -> str:
    """Generate a cryptographically secure random key.

    Uses Python's secrets module which is specifically designed for
    generating cryptographically strong random numbers suitable for
    managing secrets such as account authentication, tokens, and similar.

    Args:
        length: Number of random bytes (default: 32 = 256 bits)

    Returns:
        str: Hex-encoded random key (length * 2 characters)

    Example:
        >>> key = generate_key(32)
        >>> len(key)
        64
        >>> key.isalnum()
        True
    """
    return secrets.token_hex(length)


def validate_key(key: str) -> tuple[bool, str]:
    """Validate if a key meets security requirements.

    Args:
        key: The secret key to validate

    Returns:
        tuple: (is_valid, message)
            - is_valid: True if key passes all checks
            - message: Success message or error description
    """
    if not key:
        return False, "❌ Key is empty"

    if len(key) < 32:
        return False, f"❌ Key too short: {len(key)} chars (minimum: 32)"

    weak_keys = [
        "secret", "password", "your-super-secret-key",
        "change-me", "default", "test", "development"
    ]

    if key.lower() in weak_keys:
        return False, f"❌ Key appears to be a weak/default value"

    # Check entropy
    if key == key.lower() or key == key.upper():
        return True, "⚠️  Key valid but has low entropy (all same case)"

    return True, "✅ Key meets security requirements"


def print_env_format(key: str) -> None:
    """Print the key in .env file format.

    Args:
        key: The generated secret key
    """
    print("\n# Add this to your .env file:")
    print(f"JWT_SECRET_KEY={key}")
    print("JWT_ALGORITHM=HS256")
    print("JWT_EXPIRATION_MINUTES=30")
    print("\n# Or set via shell:")
    print(f"export JWT_SECRET_KEY={key}")


def check_current_environment() -> None:
    """Check if the current environment has a valid JWT_SECRET_KEY."""
    key = os.getenv("JWT_SECRET_KEY")

    if not key:
        print("❌ JWT_SECRET_KEY not set in environment")
        print("\nGenerate a new key with:")
        print("  python generate_secret_key.py --env")
        sys.exit(1)

    is_valid, message = validate_key(key)

    print(f"\nCurrent JWT_SECRET_KEY validation:")
    print(f"  Length: {len(key)} characters")
    print(f"  Status: {message}")

    if is_valid:
        print("\n✅ Environment is properly configured")
        sys.exit(0)
    else:
        print("\n🔧 Action required: Generate a new secure key")
        print("  python generate_secret_key.py --env")
        sys.exit(1)


def main() -> None:
    """Main entry point for the key generation utility."""
    parser = argparse.ArgumentParser(
        description="Generate cryptographically secure JWT secret keys",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a secure key
  python generate_secret_key.py

  # Generate key in .env format
  python generate_secret_key.py --env

  # Check current environment key
  python generate_secret_key.py --check

  # Generate a longer key (512 bits)
  python generate_secret_key.py --length 64

Security Notes:
  - Minimum recommended length: 32 bytes (256 bits)
  - Keys are generated using Python's secrets module
  - Never commit actual keys to version control
  - Use different keys for dev/staging/production
  - Rotate keys periodically (every 90 days recommended)
        """
    )

    parser.add_argument(
        "--length",
        type=int,
        default=32,
        help="Number of random bytes (default: 32). "
             "Output length will be double (hex encoding)"
    )

    parser.add_argument(
        "--env",
        action="store_true",
        help="Output in .env file format"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if current environment key is secure"
    )

    args = parser.parse_args()

    # Check mode
    if args.check:
        check_current_environment()
        return

    # Generate mode
    if args.length < 16:
        print("⚠️  Warning: Length < 16 bytes (128 bits) is not recommended")
        print("   Using minimum safe length of 16 bytes")
        args.length = 16

    key = generate_key(args.length)

    # Validate generated key
    is_valid, message = validate_key(key)
    assert is_valid, "Generated key failed validation"  # Should never happen

    # Output
    if args.env:
        print_env_format(key)
    else:
        print(f"\n🔐 Generated secure JWT secret key:")
        print(f"\n{key}")
        print(f"\nLength: {len(key)} characters ({args.length} bytes)")
        print(f"Entropy: {args.length * 8} bits")
        print(f"\nTo use this key, set environment variable:")
        print(f"  export JWT_SECRET_KEY={key}")
        print(f"\nOr add to .env file:")
        print(f"  JWT_SECRET_KEY={key}")

    print("\n✅ Key generation successful")


if __name__ == "__main__":
    main()
