import os
import logging
import socket

# Certificate storage directory (kept for compatibility)
CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")


class EncryptionManager:
    """Client-side encryption manager without encryption"""

    def __init__(self, use_ssl=False):
        """Initialize client encryption manager (encryption disabled)"""
        self.use_ssl = False  # Force SSL off

        # Create a valid-format Fernet key
        self.encryption_key = b'dummyKeyThatIsExactly32BytesLongs='

        # For compatibility - no real Fernet used
        self.cipher_suite = self

    def set_encryption_key(self, key):
        """Set encryption key (storing but not using for actual encryption)"""
        # Store the key but don't attempt to create a real Fernet cipher
        self.encryption_key = key

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
        return "dummy_hash_value"

    def verify_hash(self, data, hash_value):
        """Always verify hash as true for compatibility"""
        return True

    def create_temp_cert_file(self, cert_data):
        """No-op function for compatibility"""
        return None

    def wrap_socket(self, sock, server_hostname=None, cert_data=None):
        """Return socket as-is without SSL wrapping"""
        return sock


# Standalone functions for backward compatibility
def hash_data(data):
    """Standalone hash function"""
    return "dummy_hash_value"


def verify_hash(data, hash_value):
    """Verify hash (always returns True)"""
    return True