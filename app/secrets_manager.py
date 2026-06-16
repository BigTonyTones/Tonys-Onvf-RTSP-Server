"""
secrets_manager.py — Encryption-at-rest helper for sensitive credentials.

Used to store secrets (e.g. UniFi NVR SSH passwords) in camera_config.json
without leaving them in plaintext. A Fernet symmetric key is generated on first
use and stored alongside the config in data/.secret.key with 0600 permissions.

NOTE: This is encryption *at rest* (obfuscation), not a secrets vault. The app
must be able to decrypt the value in order to use it, so anyone with read access
to BOTH the config file and the key file can recover the plaintext. The key file
is kept out of version control (.gitignore) and locked to the owner. For stronger
guarantees, an SSH key (no stored password) would be required.
"""

import os
import logging

from .config import DATA_DIR

logger = logging.getLogger(__name__)

KEY_FILE = os.path.join(DATA_DIR, ".secret.key")

try:
    from cryptography.fernet import Fernet, InvalidToken
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False
    InvalidToken = Exception  # type: ignore


class SecretsManager:
    """Lazily-initialised Fernet wrapper. Thread-safe enough for our use
    (key is created once; encrypt/decrypt are stateless after that)."""

    def __init__(self, key_file: str = KEY_FILE):
        self.key_file = key_file
        self._fernet = None

    @property
    def available(self) -> bool:
        """True if the cryptography library is installed."""
        return _HAS_CRYPTO

    def _get_fernet(self):
        if not _HAS_CRYPTO:
            raise RuntimeError(
                "The 'cryptography' package is not installed. "
                "Install it with: pip install cryptography"
            )
        if self._fernet is None:
            self._fernet = Fernet(self._load_or_create_key())
        return self._fernet

    def _load_or_create_key(self) -> bytes:
        # Reuse an existing key if present.
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"[Secrets] Failed to read key file: {e}")
                raise

        # Generate a fresh key and lock it down to the owner.
        key = Fernet.generate_key()
        try:
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, "wb") as f:
                f.write(key)
            try:
                os.chmod(self.key_file, 0o600)
            except Exception:
                # chmod is a no-op / unsupported on some Windows setups; ignore.
                pass
        except Exception as e:
            logger.error(f"[Secrets] Failed to create key file: {e}")
            raise
        return key

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string, returning a token safe to store as JSON text."""
        if plaintext is None:
            return ""
        token = self._get_fernet().encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypt a token produced by encrypt(). Returns '' on failure."""
        if not token:
            return ""
        try:
            return self._get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.warning("[Secrets] Could not decrypt token (key changed or corrupt).")
            return ""
        except Exception as e:
            logger.warning(f"[Secrets] Decrypt error: {e}")
            return ""


# Module-level singleton — import and reuse.
secrets_manager = SecretsManager()
