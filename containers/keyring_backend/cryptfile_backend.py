"""Standalone keyring backend for loop-engine's containerized deployments.

Deliberately NOT part of the installed loop_engine package. Only
src/loop_engine/tools/llm/client.py is permitted to import `keyring`; this
module lives outside that boundary entirely and is wired into `keyring` via
its own backend-discovery config (keyringrc.cfg + PYTHONPATH), never
imported by loop_engine's own code.

Both the encrypted data file and the passphrase used to derive the
decryption key must be supplied as mounted files, never environment
variables — only the *paths* to those files may come from the environment.
"""

import base64
import json
import os
from pathlib import Path

import keyring.backend
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# OWASP's 2023 minimum recommendation for PBKDF2-HMAC-SHA256.
_PBKDF2_ITERATIONS = 480_000
_SALT_BYTES = 16
_ENTRY_SEPARATOR = "\0"


def _derive_key(passphrase: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_PBKDF2_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(passphrase))


class EncryptedFileKeyring(keyring.backend.KeyringBackend):
    priority = 1

    def __init__(self) -> None:
        super().__init__()
        self._file_path = Path(
            os.environ.get("LOOP_ENGINE_KEYRING_FILE", "/run/secrets/keyring_data.enc")
        )
        self._passphrase_path = Path(
            os.environ.get("LOOP_ENGINE_KEYRING_PASSPHRASE_FILE", "/run/secrets/keyring_passphrase")
        )

    def _passphrase(self) -> bytes:
        return self._passphrase_path.read_bytes().strip()

    def _load_container(self) -> dict[str, str | None]:
        if not self._file_path.exists():
            return {
                "salt": base64.urlsafe_b64encode(os.urandom(_SALT_BYTES)).decode(),
                "ciphertext": None,
            }
        return json.loads(self._file_path.read_text())

    def _load_secrets(self) -> dict[str, str]:
        container = self._load_container()
        if container["ciphertext"] is None:
            return {}
        salt = base64.urlsafe_b64decode(container["salt"])
        key = _derive_key(self._passphrase(), salt)
        try:
            decrypted = Fernet(key).decrypt(container["ciphertext"].encode())
        except InvalidToken:
            return {}
        return json.loads(decrypted.decode())

    def _save_secrets(self, secrets: dict[str, str]) -> None:
        container = self._load_container()
        salt = base64.urlsafe_b64decode(container["salt"])
        key = _derive_key(self._passphrase(), salt)
        ciphertext = Fernet(key).encrypt(json.dumps(secrets).encode()).decode()
        self._file_path.write_text(
            json.dumps({"salt": container["salt"], "ciphertext": ciphertext})
        )

    def get_password(self, service: str, username: str) -> str | None:
        return self._load_secrets().get(f"{service}{_ENTRY_SEPARATOR}{username}")

    def set_password(self, service: str, username: str, password: str) -> None:
        secrets = self._load_secrets()
        secrets[f"{service}{_ENTRY_SEPARATOR}{username}"] = password
        self._save_secrets(secrets)

    def delete_password(self, service: str, username: str) -> None:
        secrets = self._load_secrets()
        secrets.pop(f"{service}{_ENTRY_SEPARATOR}{username}", None)
        self._save_secrets(secrets)
