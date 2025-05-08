"""
Encryption utilities for the Central Management Server.
Handles SSL/TLS encryption and message-level encryption with Fernet.
"""

import ssl
import socket
import hashlib
import os
import logging
import tempfile
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta

# Certificate paths
CERT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "certs")
CERT_FILE = os.path.join(CERT_DIR, "server.crt")
KEY_FILE = os.path.join(CERT_DIR, "server.key")

class EncryptionManager:
    """Encryption manager with automatic SSL certificate generation"""

    def __init__(self, use_ssl=True):
        """Initialize encryption manager with SSL and Fernet support"""
        self.use_ssl = use_ssl

        # Create Fernet key for message-level encryption
        self.encryption_key = self.create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # Ensure certificate directory exists
        if not os.path.exists(CERT_DIR):
            os.makedirs(CERT_DIR, exist_ok=True)

        # Auto-generate certificate if needed
        if use_ssl and (not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE)):
            self.generate_certificate()

    def create_encryption_key(self):
        """Generate a new Fernet encryption key"""
        return Fernet.generate_key()

    def encrypt_data(self, data):
        """Encrypt data using Fernet cipher suite"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher_suite.encrypt(data)

    def decrypt_data(self, encrypted_data):
        """Decrypt data using Fernet cipher suite"""
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

    def generate_certificate(self):
        """Generate a self-signed certificate for the server"""
        try:
            logging.info("Generating new SSL certificate...")

            # Create private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            # Get hostname for certificate
            hostname = socket.gethostname()

            # Define certificate subject
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NetControl Central Server"),
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ])

            # Build certificate
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(hostname),
                    x509.DNSName("localhost")
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())

            # Write certificate and private key to files
            with open(CERT_FILE, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))

            with open(KEY_FILE, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            # Set restrictive permissions on key file if on Unix-like systems
            if os.name == 'posix':
                os.chmod(KEY_FILE, 0o600)

            logging.info(f"SSL certificate generated at {CERT_FILE}")
            logging.info(f"Private key saved to {KEY_FILE}")

            return True

        except Exception as e:
            logging.error(f"Failed to generate certificate: {e}")
            return False

    def wrap_socket(self, sock):
        """Wrap a socket with SSL for server-side"""
        if not self.use_ssl:
            return sock

        if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
            logging.error("SSL certificate files not found")
            logging.info("Attempting to regenerate certificates...")
            if not self.generate_certificate():
                logging.error("Failed to generate certificates, SSL disabled")
                return sock

        try:
            # Create an SSL context
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)

            # Wrap the socket
            wrapped_socket = context.wrap_socket(sock, server_side=True)
            logging.info("Successfully enabled SSL encryption")
            return wrapped_socket
        except Exception as e:
            logging.error(f"SSL configuration error: {e}")
            return sock

    def get_certificate_data(self):
        """Get the server's certificate data to share with clients"""
        try:
            if os.path.exists(CERT_FILE):
                with open(CERT_FILE, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logging.error(f"Error reading certificate: {e}")
            return None