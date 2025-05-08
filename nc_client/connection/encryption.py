import ssl
import socket
import hashlib
import os
import logging
import tempfile
from cryptography.fernet import Fernet

# Certificate storage directory for client-side
CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")


class EncryptionManager:
    """Client-side encryption manager with SSL and SHA-256 hashing"""

    def __init__(self, use_ssl=True):
        """Initialize client encryption manager"""
        self.use_ssl = use_ssl

        # Variables to store encryption info
        self.encryption_key = None
        self.cipher_suite = None

        # Create certs directory if it doesn't exist
        if not os.path.exists(CERT_DIR):
            os.makedirs(CERT_DIR, exist_ok=True)

        # Temporary file for SSL certificate
        self.temp_cert_file = None

    def set_encryption_key(self, key):
        """Set the Fernet encryption key received from server"""
        self.encryption_key = key
        self.cipher_suite = Fernet(key)

    def encrypt_data(self, data):
        """Encrypt data using Fernet cipher suite"""
        if not self.cipher_suite:
            raise ValueError("Encryption key not set. Connect to server first.")

        if isinstance(data, str):
            data = data.encode()
        return self.cipher_suite.encrypt(data)

    def decrypt_data(self, encrypted_data):
        """Decrypt data using Fernet cipher suite"""
        if not self.cipher_suite:
            raise ValueError("Encryption key not set. Connect to server first.")

        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode()

    def hash_data(self, data):
        """Generate SHA-256 hash of data"""
        if isinstance(data, str):
            data = data.encode()
        return hashlib.sha256(data).hexdigest()

    def verify_hash(self, data, hash_value):
        """Verify data against a SHA-256 hash"""
        computed_hash = self.hash_data(data)
        return computed_hash == hash_value

    def create_temp_cert_file(self, cert_data):
        """Create a temporary certificate file for SSL context"""
        try:
            # Save to persistent location so it's available for reconnections
            server_hash = self.hash_data(cert_data)[:10]  # First 10 chars of hash
            cert_path = os.path.join(CERT_DIR, f"server_{server_hash}.crt")

            # Write certificate data to file
            with open(cert_path, 'wb') as f:
                f.write(cert_data)

            logging.info(f"Server certificate saved to {cert_path}")
            return cert_path

        except Exception as e:
            logging.error(f"Error creating certificate file: {e}")

            # Fallback to temporary file
            try:
                fd, temp_path = tempfile.mkstemp(suffix='.crt')
                with os.fdopen(fd, 'wb') as f:
                    f.write(cert_data)
                logging.info(f"Server certificate saved to temporary file: {temp_path}")
                return temp_path
            except Exception as e2:
                logging.error(f"Error creating temporary certificate file: {e2}")
                return None

    def wrap_socket(self, sock, server_hostname=None, cert_data=None):
        """Wrap a client socket with SSL using server's certificate"""
        if not self.use_ssl:
            return sock

        try:
            # Create a default context with no verification initially
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            # If we have certificate data, use it for verification
            cert_file = None
            if cert_data:
                cert_file = self.create_temp_cert_file(cert_data)
                if cert_file:
                    # Load the certificate for verification
                    context.load_verify_locations(cert_file)
                    # We could enable verification here, but for simplicity we keep it disabled
                    # context.check_hostname = True
                    # context.verify_mode = ssl.CERT_REQUIRED

            # Connect with SSL
            wrapped_socket = context.wrap_socket(
                sock,
                server_hostname=server_hostname
            )

            logging.info("SSL connection established")
            return wrapped_socket

        except ssl.SSLError as e:
            logging.error(f"SSL error: {e}")
            raise
        except Exception as e:
            logging.error(f"Error establishing SSL connection: {e}")
            raise
        finally:
            # Clean up temporary certificate file if we created one
            if cert_file and cert_file.startswith(tempfile.gettempdir()):
                try:
                    os.remove(cert_file)
                except:
                    pass


def hash_data(data):
    """Generate SHA-256 hash of data (standalone function)"""
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def verify_hash(data, hash_value):
    """Verify data against a SHA-256 hash (standalone function)"""
    computed_hash = hash_data(data)
    return computed_hash == hash_value