"""
Simplified encryption utilities for the NC Server.
This version removes actual encryption for simplified communication.
"""

import os
import logging
import socket

# Certificate paths (kept for API compatibility)
CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")


class EncryptionManager:
    """Encryption manager with encryption functionality removed"""

    def __init__(self, use_ssl=False):
        """Initialize encryption manager (without encryption)"""
        self.use_ssl = False  # Force SSL off

        # Create a valid Fernet key format (base64-encoded 32 bytes)
        self.encryption_key = b'dummyKeyThatIsExactly32BytesLongs='

        # For compatibility - no real Fernet used
        self.cipher_suite = self

    def create_encryption_key(self):
        """Generate a dummy encryption key"""
        return self.encryption_key

    def encrypt_data(self, data):
        """No-op encrypt function"""
        if isinstance(data, str):
            data = data.encode()
        return data

    def decrypt_data(self, encrypted_data):
        """No-op decrypt function"""
        if isinstance(encrypted_data, bytes):
            try:
                return encrypted_data.decode()
            except UnicodeDecodeError:
                return str(encrypted_data)
        return str(encrypted_data)

    def encrypt(self, data):
        """Alias for encrypt_data (for compatibility)"""
        return self.encrypt_data(data)

    def decrypt(self, data):
        """Alias for decrypt_data (for compatibility)"""
        return self.decrypt_data(data)

    def hash_data(self, data):
        """Simple hash for compatibility"""
        if isinstance(data, str):
            data = data.encode()
        # Return a fixed hash for simplicity
        return "dummy_hash_value"

    def verify_hash(self, data, hash_value):
        """Always verify hash as true for compatibility"""
        return True

    def generate_certificate(self):
        """Dummy certificate generation"""
        logging.info("Certificate generation skipped (encryption disabled)")
        return True

    def wrap_socket(self, sock):
        """Return the socket as-is without SSL wrapping"""
        logging.info("SSL wrapping skipped (encryption disabled)")
        return sock

    def get_certificate_data(self):
        """Return dummy certificate data"""
        return b'dummy_certificate_data'


# Legacy functions for backwards compatibility
def create_encryption_key():
    """Legacy function for compatibility"""
    return b'dummyKeyThatIsExactly32BytesLongs='


def encrypt_data(cipher_suite, data):
    """Legacy function for compatibility"""
    if isinstance(data, str):
        data = data.encode()
    return data


def decrypt_data(cipher_suite, encrypted_data):
    """Legacy function for compatibility"""
    if isinstance(encrypted_data, bytes):
        try:
            return encrypted_data.decode()
        except UnicodeDecodeError:
            return str(encrypted_data)
    return str(encrypted_data)