"""
Smoke test for secrets_resolver + feature_toggles.
Tests: default path, mutual exclusion guard, and encrypted file round-trip.
"""
import os, sys, base64, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Test 1: default source (no toggles) ──────────────────────────────────────
os.environ["FEATURES_DB_AWS_SECRETS_MGR_ENABLED"] = "false"
os.environ["FEATURES_DB_AZURE_KEY_VAULT_ENABLED"]  = "false"
os.environ["FEATURES_DB_GCP_SECRET_MGR_ENABLED"]   = "false"
os.environ["FEATURES_DB_ENCRYPTED_FILE_ENABLED"]   = "false"

from app.app_common.config.feature_toggles import FeatureToggles
FeatureToggles.reload()
assert FeatureToggles.active_secrets_source() is None, "Expected None source"
print("✓ Test 1 passed: default source = plain env / .env")

# ── Test 2: mutual exclusion guard ───────────────────────────────────────────
os.environ["FEATURES_DB_AWS_SECRETS_MGR_ENABLED"] = "true"
os.environ["FEATURES_DB_AZURE_KEY_VAULT_ENABLED"]  = "true"
FeatureToggles.reload()
try:
    FeatureToggles.active_secrets_source()
    assert False, "Should have raised ValueError"
except ValueError as e:
    print(f"✓ Test 2 passed: mutual exclusion guard raised ValueError: {e}")

# ── Test 3: encrypted file round-trip ────────────────────────────────────────
os.environ["FEATURES_DB_AWS_SECRETS_MGR_ENABLED"] = "false"
os.environ["FEATURES_DB_AZURE_KEY_VAULT_ENABLED"]  = "false"
os.environ["FEATURES_DB_ENCRYPTED_FILE_ENABLED"]   = "true"
FeatureToggles.reload()
assert FeatureToggles.active_secrets_source() == "encrypted_file"

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    import tempfile

    # Encrypt a test payload
    key = os.urandom(32)
    key_b64 = base64.b64encode(key).decode()
    payload = {"DATABASE_URL": "sqlite:///test.db", "TEST_KEY": "hello"}
    plaintext = json.dumps(payload).encode()
    nonce = os.urandom(12)
    ct_tag = AESGCM(key).encrypt(nonce, plaintext, None)
    envelope = {
        "nonce":      base64.b64encode(nonce).decode(),
        "ciphertext": base64.b64encode(ct_tag[:-16]).decode(),
        "tag":        base64.b64encode(ct_tag[-16:]).decode(),
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".enc.json", delete=False) as f:
        json.dump(envelope, f)
        enc_path = f.name

    os.environ["SECRETS_ENCRYPTED_FILE_PATH"] = enc_path
    os.environ["SECRETS_ENCRYPTION_KEY"]       = key_b64

    # Remove any previously cached resolution
    import app.app_common.config.secrets_resolver as sr
    sr._resolved = False
    # Remove injected keys so we can verify injection
    os.environ.pop("TEST_KEY", None)

    sr.resolve_secrets()

    assert os.environ.get("TEST_KEY") == "hello", "Decrypted TEST_KEY mismatch"
    print("✓ Test 3 passed: encrypted file round-trip decryption works")

    os.unlink(enc_path)
except ImportError:
    print("⚠  Test 3 skipped: 'cryptography' not installed (pip install cryptography)")

print("\n✓ All smoke tests passed.")
