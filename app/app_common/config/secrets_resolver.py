"""
secrets_resolver.py
====================
Class-based secrets resolution. SecretsResolver is a singleton that resolves
application secrets from exactly one provider chosen by FeatureToggles.
All provider logic is encapsulated as private methods of the class.
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Dict, Optional

from app.app_common.config.feature_toggles import FeatureToggles

logger = logging.getLogger(__name__)


class SecretsResolver:
    """
    Singleton that resolves secrets from exactly one source and injects
    them into os.environ.  Call SecretsResolver.instance().resolve() once
    at startup; subsequent calls are no-ops.

    Providers (chosen by FeatureToggles — exactly one may be active):
      - Plain .env / os.environ          (default, no toggle needed)
      - AWS Secrets Manager              FEATURES_DB_AWS_SECRETS_MGR_ENABLED=true
      - Azure Key Vault                  FEATURES_DB_AZURE_KEY_VAULT_ENABLED=true
      - GCP Secret Manager               FEATURES_DB_GCP_SECRET_MGR_ENABLED=true
      - AES-256-GCM encrypted JSON file  FEATURES_DB_ENCRYPTED_FILE_ENABLED=true

    Secret payload (JSON object, same for all cloud providers + encrypted file):
      { "DATABASE_URL": "...", "YOUTUBE_API_KEY": "..." }
    """

    _instance: Optional["SecretsResolver"] = None
    _initialised: bool = False

    def __new__(cls) -> "SecretsResolver":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialised:
            return
        self._initialised = True
        self._resolved: bool = False

    @classmethod
    def instance(cls) -> "SecretsResolver":
        return cls()

    # ── Public API ───────────────────────────────────────────────────────────

    def resolve(self) -> None:
        """
        Load secrets from the active provider and inject into os.environ.
        Safe to call multiple times — executes only on the first call.
        """
        if self._resolved:
            return
        self._resolved = True

        source = FeatureToggles.active_secrets_source()
        if source is None:
            logger.info("[SecretsResolver] Source: plain .env / environment (default)")
            return

        logger.info("[SecretsResolver] Source: %s", source)
        secrets = self._load(source)
        self._inject(secrets)
        logger.info("[SecretsResolver] Injected %d secret(s) from %s", len(secrets), source)

    def get_secret(self, key: str, default: str = "") -> str:
        """Resolve secrets then return os.environ.get(key)."""
        self.resolve()
        return os.environ.get(key, default)

    def reset(self) -> None:
        """Reset resolved flag — useful in tests."""
        self._resolved = False

    # ── Private dispatch ─────────────────────────────────────────────────────

    def _load(self, source: str) -> Dict[str, str]:
        loaders = {
            "aws_secrets_manager": self._load_aws,
            "azure_key_vault":     self._load_azure,
            "gcp_secret_manager":  self._load_gcp,
            "encrypted_file":      self._load_encrypted_file,
        }
        return loaders[source]()

    def _inject(self, secrets: Dict[str, str]) -> None:
        for key, value in secrets.items():
            if key not in os.environ:   # never overwrite explicit env overrides
                os.environ[key] = str(value)

    # ── Provider: AWS Secrets Manager ────────────────────────────────────────

    def _load_aws(self) -> Dict[str, str]:
        try:
            import boto3                                    # type: ignore
            from botocore.exceptions import ClientError    # type: ignore
        except ImportError:
            raise ImportError(
                "[SecretsResolver] AWS Secrets Manager enabled but 'boto3' not installed. "
                "Run: pip install boto3"
            )
        secret_name = os.environ.get("AWS_SECRETS_MGR_SECRET_NAME")
        region      = os.environ.get("AWS_REGION", "us-east-1")
        if not secret_name:
            raise ValueError(
                "[SecretsResolver] AWS_SECRETS_MGR_SECRET_NAME is required "
                "when FEATURES_DB_AWS_SECRETS_MGR_ENABLED=true"
            )
        client = boto3.client("secretsmanager", region_name=region)
        try:
            response = client.get_secret_value(SecretId=secret_name)
        except ClientError as e:
            raise RuntimeError(f"[SecretsResolver] AWS Secrets Manager error: {e}") from e
        raw = response.get("SecretString") or base64.b64decode(response["SecretBinary"]).decode()
        return self._parse_json(raw, "AWS Secrets Manager")

    # ── Provider: Azure Key Vault ─────────────────────────────────────────────

    def _load_azure(self) -> Dict[str, str]:
        try:
            from azure.keyvault.secrets import SecretClient      # type: ignore
            from azure.identity import DefaultAzureCredential    # type: ignore
        except ImportError:
            raise ImportError(
                "[SecretsResolver] Azure Key Vault enabled but packages missing. "
                "Run: pip install azure-keyvault-secrets azure-identity"
            )
        vault_url   = os.environ.get("AZURE_KEY_VAULT_URL")
        secret_name = os.environ.get("AZURE_KEY_VAULT_SECRET_NAME", "app-secrets")
        if not vault_url:
            raise ValueError(
                "[SecretsResolver] AZURE_KEY_VAULT_URL is required "
                "when FEATURES_DB_AZURE_KEY_VAULT_ENABLED=true"
            )
        client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
        try:
            secret = client.get_secret(secret_name)
        except Exception as e:
            raise RuntimeError(f"[SecretsResolver] Azure Key Vault error: {e}") from e
        return self._parse_json(secret.value or "{}", "Azure Key Vault")

    # ── Provider: GCP Secret Manager ─────────────────────────────────────────

    def _load_gcp(self) -> Dict[str, str]:
        try:
            from google.cloud import secretmanager    # type: ignore
        except ImportError:
            raise ImportError(
                "[SecretsResolver] GCP Secret Manager enabled but package missing. "
                "Run: pip install google-cloud-secret-manager"
            )
        project_id  = os.environ.get("GCP_PROJECT_ID")
        secret_name = os.environ.get("GCP_SECRET_NAME")
        version     = os.environ.get("GCP_SECRET_VERSION", "latest")
        if not project_id or not secret_name:
            raise ValueError(
                "[SecretsResolver] GCP_PROJECT_ID and GCP_SECRET_NAME are required "
                "when FEATURES_DB_GCP_SECRET_MGR_ENABLED=true"
            )
        client   = secretmanager.SecretManagerServiceClient()
        resource = f"projects/{project_id}/secrets/{secret_name}/versions/{version}"
        try:
            response = client.access_secret_version(request={"name": resource})
        except Exception as e:
            raise RuntimeError(f"[SecretsResolver] GCP Secret Manager error: {e}") from e
        return self._parse_json(response.payload.data.decode("utf-8"), "GCP Secret Manager")

    # ── Provider: Encrypted JSON file (AES-256-GCM) ──────────────────────────

    def _load_encrypted_file(self) -> Dict[str, str]:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM    # type: ignore
        except ImportError:
            raise ImportError(
                "[SecretsResolver] Encrypted file enabled but 'cryptography' not installed. "
                "Run: pip install cryptography"
            )
        file_path   = os.environ.get("SECRETS_ENCRYPTED_FILE_PATH")
        encoded_key = os.environ.get("SECRETS_ENCRYPTION_KEY")
        if not file_path or not encoded_key:
            raise ValueError(
                "[SecretsResolver] SECRETS_ENCRYPTED_FILE_PATH and SECRETS_ENCRYPTION_KEY "
                "are required when FEATURES_DB_ENCRYPTED_FILE_ENABLED=true"
            )
        try:
            key = base64.b64decode(encoded_key)
            with open(file_path, "r") as f:
                envelope = json.load(f)
            nonce      = base64.b64decode(envelope["nonce"])
            ciphertext = base64.b64decode(envelope["ciphertext"])
            tag        = base64.b64decode(envelope["tag"])
            plaintext  = AESGCM(key).decrypt(nonce, ciphertext + tag, None)
        except (KeyError, ValueError, OSError) as e:
            raise RuntimeError(f"[SecretsResolver] Encrypted file decryption error: {e}") from e
        return self._parse_json(plaintext.decode("utf-8"), "encrypted file")

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(raw: str, source_label: str) -> Dict[str, str]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"[SecretsResolver] Payload from {source_label} is not valid JSON: {e}"
            ) from e
        if not isinstance(data, dict):
            raise ValueError(
                f"[SecretsResolver] Payload from {source_label} must be a JSON object."
            )
        return {str(k): str(v) for k, v in data.items()}


# ---------------------------------------------------------------------------
# Module-level convenience — preserves the resolve_secrets() call sites
# in main.py, db_engine.py and migrations/env.py unchanged.
# ---------------------------------------------------------------------------
def resolve_secrets() -> None:
    SecretsResolver.instance().resolve()


def get_secret(key: str, default: str = "") -> str:
    return SecretsResolver.instance().get_secret(key, default)
