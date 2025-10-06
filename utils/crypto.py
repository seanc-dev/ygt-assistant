from typing import Tuple
from cryptography.fernet import Fernet


def fernet_from(key_str: str | None) -> Tuple[Fernet, str]:
    """
    Returns a Fernet instance and the base64 key used.
    If key_str is falsy, generate a new key (good for tests).
    """

    if key_str:
        key = key_str.encode()
    else:
        key = Fernet.generate_key()
    return Fernet(key), key.decode()


def encrypt(fernet: Fernet, plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt(fernet: Fernet, ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()


