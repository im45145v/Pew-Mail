from cryptography.fernet import Fernet
from app.core.config import settings
import base64
import os

class TokenEncryption:
    """Handles encryption and decryption of Google OAuth tokens"""
    
    def __init__(self):
        # Use the SECRET_KEY from settings, but ensure it's 32 url-safe base64-encoded bytes
        key = settings.SECRET_KEY.encode()
        # Ensure the key is exactly 32 bytes by hashing it
        import hashlib
        self.key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, token: str) -> str:
        """Encrypt a token"""
        if not token:
            return None
        encrypted_token = self.cipher_suite.encrypt(token.encode())
        return encrypted_token.decode()
    
    def decrypt(self, encrypted_token: str) -> str:
        """Decrypt a token"""
        if not encrypted_token:
            return None
        decrypted_token = self.cipher_suite.decrypt(encrypted_token.encode())
        return decrypted_token.decode()