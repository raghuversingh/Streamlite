import os
from pathlib import Path
from cryptography.fernet import Fernet
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
KEY_FILE = ROOT / "encryption.key"
ENV_FILE = ROOT / ".env"


def _load_env():
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE)


def get_encryption_key():
    _load_env()
    key = os.getenv("DATA_ENCRYPTION_KEY")
    if key:
        return key.encode()
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    new_key = Fernet.generate_key()
    KEY_FILE.write_bytes(new_key)
    return new_key


def get_fernet():
    return Fernet(get_encryption_key())


def encrypt_string(text):
    if text is None:
        return None
    return get_fernet().encrypt(text.encode()).decode()


def decrypt_string(token):
    if token is None:
        return None
    try:
        return get_fernet().decrypt(token.encode()).decode()
    except Exception:
        return token
