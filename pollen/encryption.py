import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import utils

import paths
from logger import Logger


class PollenEncryptionException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class PollenEncryption:
    def __init__(self):
        self._logger = Logger("Pollen")
        self._private_key = self._load_private_key()
        if self._private_key is not None:
            self._public_key = self._private_key.public_key()

    def _load_private_key(self):
        private_key = None
        path = os.path.join(paths.ROOT_DIR, "private_key.pem")
        if os.path.isfile(path):
            try:
                with open(path) as key_file:
                    private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
            except:
                self._logger.error("Failed to load private key from {}"
                                   .format(path))
        else:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            with open(path, "wb") as key_file:
                key_file.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
        return private_key

    def get_serialized_public_key(self):
        return self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def encrypt(self, data, serialized_public_key):
        public_key = serialization.load_pem_public_key(
            serialized_public_key,
            backend=default_backend()
        )
        symmetric_key = Fernet.generate_key()
        encrypted_symmetric_key = base64.b64encode(
            public_key.encrypt(
                bytes(symmetric_key),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        )
        cipher = Fernet(symmetric_key)
        encrypted_data = cipher.encrypt(bytes(data))
        hasher = hashes.Hash(hashes.SHA256(), default_backend())
        hasher.update(data)
        data_digest = hasher.finalize()
        signature = base64.b64encode(
            self._private_key.sign(
                data_digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                utils.Prehashed(hashes.SHA256())
            )
        )
        return {"encrypted_symmetric_key": encrypted_symmetric_key,
                "signature": signature,
                "encrypted_data": encrypted_data}

    def decrypt(self, encrypted_data):
        message_keys = ["encrypted_symmetric_key",
                        "signature",
                        "encrypted_data"]
        if any(key not in encrypted_data for key in message_keys):
            raise PollenEncryptionException("Unable to decrypt malformed data")
        symmetric_key = self._private_key.decrypt(
            base64.b64decode(encrypted_data['encrypted_symmetric_key']),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        try:
            cipher = Fernet(symmetric_key)
            return cipher.decrypt(bytes(encrypted_data['encrypted_data']))
        except:
            pass
        return None


