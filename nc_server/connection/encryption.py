from cryptography.fernet import Fernet

def create_encryption_key():
    """Generate a new Fernet encryption key"""
    return Fernet.generate_key()

def encrypt_data(cipher_suite, data):
    """Encrypt data using Fernet cipher suite"""
    if isinstance(data, str):
        data = data.encode()
    return cipher_suite.encrypt(data)

def decrypt_data(cipher_suite, encrypted_data):
    """Decrypt data using Fernet cipher suite"""
    decrypted_data = cipher_suite.decrypt(encrypted_data)
    return decrypted_data.decode()