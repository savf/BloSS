import json

import ipfsapi
from ipfsapi.exceptions import ConnectionError, ProtocolError, TimeoutError

from configuration import Configuration
from logger import Logger


class PollenDatastore:

    def __init__(self, encryption=None):
        self._config = Configuration()
        self._logger = Logger("Pollen")
        self.connection = ipfsapi.connect(self._config['DATASTORE']['HOST'],
                                          self._config['DATASTORE']['PORT'])
        self._encryption = encryption

    def store(self, data, to_sign=None, serialized_public_key=None):
        try:
            if all([to_sign, serialized_public_key, self._encryption]):
                data = self._encryption.encrypt(to_sign,
                                                data,
                                                serialized_public_key)
                self._logger.info("Encrypted attack report with hash {}."
                                  .format(to_sign))
                data = json.dumps(data)
            return self.connection.add_bytes(bytes(data))
        except (ProtocolError, ConnectionError, TimeoutError) as e:
            return ""

    def retrieve(self, ipfs_hash):
        try:
            data = self.connection.cat(ipfs_hash)
            if self._encryption is not None:
                try:
                    encrypted_payload = json.loads(data)
                    data = json.loads(
                        self._encryption.decrypt(
                            encrypted_payload=encrypted_payload
                        )
                    )
                    if type(data) == dict:
                        data['signature'] = encrypted_payload['signature']
                except:
                    pass
            return data
        except (ProtocolError, ConnectionError, TimeoutError) as e:
            return ""
