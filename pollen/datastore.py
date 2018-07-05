import json

import ipfsapi
from ipfsapi.exceptions import ConnectionError, ProtocolError, TimeoutError

from configuration import Configuration
from encryption import PollenEncryptionException
from logger import Logger


class PollenDatastore:

    def __init__(self, encryption=None):
        self._config = Configuration()
        self._logger = Logger("Pollen")
        self.connection = ipfsapi.connect(self._config['DATASTORE']['HOST'],
                                          self._config['DATASTORE']['PORT'])
        if encryption is not None:
            self._encryption = encryption

    def store(self, data, serialized_public_key=None):
        try:
            if all([serialized_public_key, self._encryption]):
                data = self._encryption.encrypt(data,
                                                serialized_public_key)
                data = json.dumps(data)
            return self.connection.add_bytes(bytes(data))
        except (ProtocolError, ConnectionError, TimeoutError) as e:
            return ""

    def retrieve(self, ipfs_hash):
        try:
            data = self.connection.cat(ipfs_hash)
            if self._encryption is not None:
                try:
                    data = json.loads(
                        self._encryption.decrypt(
                            encrypted_data=json.loads(data)
                        )
                    )
                except:
                    pass
            return data
        except (ProtocolError, ConnectionError, TimeoutError) as e:
            return ""
