import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
from .security import derive_key, generate_salt

class SecretsManager:
    """
    Manages encrypted secrets using AES-256-GCM.
    Master key is stored as hex string, loaded and decoded to bytes.
    """

    def __init__(self, secrets_path: str, master_key_path: str):
        self.secrets_path = Path(secrets_path)
        self.master_key_path = Path(master_key_path)
        self._master_key = None
        self._secrets = None

    def _load_master_key(self) -> bytes:
        """Load master key from hex file, decode to bytes."""
        if self.master_key_path.exists():
            with open(self.master_key_path, 'r') as f:
                hex_key = f.read().strip()
                return bytes.fromhex(hex_key)
        else:
            key = os.urandom(32)
            self.master_key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.master_key_path, 'w') as f:
                f.write(key.hex())
            os.chmod(self.master_key_path, 0o600)
            return key

    def _get_master_key(self) -> bytes:
        if self._master_key is None:
            self._master_key = self._load_master_key()
        return self._master_key

    def encrypt_secrets(self, secrets: Dict[str, Any]) -> None:
        key = self._get_master_key()
        nonce = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        plaintext = json.dumps(secrets).encode('utf-8')
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        payload = nonce + ciphertext + encryptor.tag
        with open(self.secrets_path, 'wb') as f:
            f.write(payload)
        os.chmod(self.secrets_path, 0o600)

    def load_secrets(self) -> Dict[str, Any]:
        if not self.secrets_path.exists():
            return {}
        key = self._get_master_key()
        with open(self.secrets_path, 'rb') as f:
            payload = f.read()
        nonce = payload[:12]
        tag = payload[-16:]
        ciphertext = payload[12:-16]
        try:
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return json.loads(plaintext.decode('utf-8'))
        except InvalidTag:
            backup = f"{self.secrets_path}.corrupted.{int(time.time())}"
            os.rename(self.secrets_path, backup)
            return {}

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        if self._secrets is None:
            self._secrets = self.load_secrets()
        return self._secrets.get(key, default)

    def set(self, key: str, value: Any) -> None:
        if self._secrets is None:
            self._secrets = self.load_secrets()
        self._secrets[key] = value
        self.encrypt_secrets(self._secrets)
