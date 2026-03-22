"""
feature_toggles.py
==================
Single source of truth for all feature flags in the app.
All toggles default to False — the standard .env / os.environ behaviour
is always the baseline.  Set exactly ONE secrets source to True.

Environment variable reference
-------------------------------
  FEATURES_DB_AWS_SECRETS_MGR_ENABLED   = true   → read secrets from AWS Secrets Manager
  FEATURES_DB_AZURE_KEY_VAULT_ENABLED   = true   → read secrets from Azure Key Vault
  FEATURES_DB_GCP_SECRET_MGR_ENABLED    = true   → read secrets from GCP Secret Manager
  FEATURES_DB_ENCRYPTED_FILE_ENABLED    = true   → read secrets from an AES-encrypted JSON file

Only one may be true at a time.  If more than one is true the app raises
a clear error at startup rather than silently picking one.
"""
from __future__ import annotations

import os


def _bool(key: str) -> bool:
    return os.environ.get(key, "false").strip().lower() in ("1", "true", "yes")


class FeatureToggles:
    """Read-only view of all feature flags.  Instantiated once at import time."""

    # ── Secrets source toggles ─────────────────────────────────────────────
    db_aws_secrets_mgr_enabled: bool = _bool("FEATURES_DB_AWS_SECRETS_MGR_ENABLED")
    db_azure_key_vault_enabled: bool = _bool("FEATURES_DB_AZURE_KEY_VAULT_ENABLED")
    db_gcp_secret_mgr_enabled:  bool = _bool("FEATURES_DB_GCP_SECRET_MGR_ENABLED")
    db_encrypted_file_enabled:  bool = _bool("FEATURES_DB_ENCRYPTED_FILE_ENABLED")

    @classmethod
    def active_secrets_source(cls) -> str | None:
        """
        Return the name of the active secrets source, or None (plain env / .env).
        Raises ValueError if more than one toggle is enabled.
        """
        active = [
            name for name, enabled in {
                "aws_secrets_manager": cls.db_aws_secrets_mgr_enabled,
                "azure_key_vault":     cls.db_azure_key_vault_enabled,
                "gcp_secret_manager":  cls.db_gcp_secret_mgr_enabled,
                "encrypted_file":      cls.db_encrypted_file_enabled,
            }.items()
            if enabled
        ]
        if len(active) > 1:
            raise ValueError(
                f"[FeatureToggles] Only ONE secrets source may be enabled at a time. "
                f"Currently enabled: {active}"
            )
        return active[0] if active else None

    @classmethod
    def reload(cls) -> None:
        """Re-read all env vars (useful in tests)."""
        cls.db_aws_secrets_mgr_enabled = _bool("FEATURES_DB_AWS_SECRETS_MGR_ENABLED")
        cls.db_azure_key_vault_enabled = _bool("FEATURES_DB_AZURE_KEY_VAULT_ENABLED")
        cls.db_gcp_secret_mgr_enabled  = _bool("FEATURES_DB_GCP_SECRET_MGR_ENABLED")
        cls.db_encrypted_file_enabled  = _bool("FEATURES_DB_ENCRYPTED_FILE_ENABLED")


# Module-level singleton
toggles = FeatureToggles()
