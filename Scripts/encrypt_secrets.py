#!/usr/bin/env python
"""
encrypt_secrets.py
==================
Encrypts a plaintext JSON secrets file using AES-256-GCM and writes an
envelope JSON file that secrets_resolver.py can decrypt at app startup.

Usage
-----
  # 1. Generate a key (do this once, store securely)
  export SECRETS_ENCRYPTION_KEY=$(python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())")
  echo $SECRETS_ENCRYPTION_KEY   # save this somewhere safe!

  # 2. Create your plaintext secrets file  (DO NOT commit this)
  cat > /tmp/secrets.json << EOF
  {
    "DATABASE_URL":    "postgresql+psycopg2://user:pass@host:5432/dbname",
    "YOUTUBE_API_KEY": "AIza..."
  }
  EOF

  # 3. Encrypt it
  python Scripts/encrypt_secrets.py /tmp/secrets.json app/data/secrets.enc.json

  # 4. Set env vars for the app
  export FEATURES_DB_ENCRYPTED_FILE_ENABLED=true
  export SECRETS_ENCRYPTED_FILE_PATH=$(pwd)/app/data/secrets.enc.json
  export SECRETS_ENCRYPTION_KEY=<the key from step 1>

  # Delete the plaintext file!
  rm /tmp/secrets.json
"""
import argparse
import base64
import json
import os
import sys

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print("ERROR: 'cryptography' not installed. Run: pip install cryptography")
    sys.exit(1)


def encrypt(plaintext_path: str, output_path: str, key_b64: str) -> None:
    key   = base64.b64decode(key_b64)
    nonce = os.urandom(12)      # 96-bit nonce, GCM standard

    with open(plaintext_path, "rb") as f:
        plaintext = f.read()

    aesgcm     = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, None)

    # AESGCM appends the 16-byte tag at the end
    ciphertext = ciphertext_with_tag[:-16]
    tag        = ciphertext_with_tag[-16:]

    envelope = {
        "nonce":      base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "tag":        base64.b64encode(tag).decode(),
    }

    with open(output_path, "w") as f:
        json.dump(envelope, f, indent=2)

    print(f"✓ Encrypted  {plaintext_path}  →  {output_path}")
    print(f"  Store SECRETS_ENCRYPTION_KEY safely — you cannot decrypt without it.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Encrypt a JSON secrets file with AES-256-GCM")
    parser.add_argument("input",  help="Path to plaintext JSON secrets file")
    parser.add_argument("output", help="Path for the encrypted output file (.enc.json)")
    args = parser.parse_args()

    key_b64 = os.environ.get("SECRETS_ENCRYPTION_KEY")
    if not key_b64:
        print("ERROR: SECRETS_ENCRYPTION_KEY env var not set.")
        print("  Generate one: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\"")
        sys.exit(1)

    encrypt(args.input, args.output, key_b64)
