"""
encryption.py — Fernet symmetric encryption for email bodies.
Takes a Flask app instance (to read SECRET_KEY) rather than importing from app.
"""
import base64, hashlib, logging
logger = logging.getLogger(__name__)

def _get_fernet(app):
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        raise RuntimeError("Install cryptography:  pip install cryptography")
    raw  = app.config['SECRET_KEY'].encode('utf-8')
    key  = base64.urlsafe_b64encode(hashlib.sha256(raw).digest())
    return Fernet(key)

def encrypt_body(app, plaintext: str) -> str:
    return _get_fernet(app).encrypt(plaintext.encode('utf-8')).decode('utf-8')

def decrypt_body(app, ciphertext: str) -> str:
    return _get_fernet(app).decrypt(ciphertext.encode('utf-8')).decode('utf-8')
