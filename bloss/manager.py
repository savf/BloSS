import json
import time
from threading import Thread

import requests

import api
from configuration import Configuration
from logger import Logger
from pollen.blockchain import PollenBlockchain


class BloSS:
    def __init__(self):
        self._config = Configuration()
        self._logger = Logger("BloSS")
        self._pollen_blockchain = PollenBlockchain(
            enable_encryption=self._config['DATASTORE']['ENCRYPTION']
        )
        retrieval_thread = Thread(target=self._retrieve_attackers_periodically)
        retrieval_thread.daemon = True
        retrieval_thread.start()
        self._api_thread = Thread(target=self._start_api)
        self._api_thread.daemon = True
        self._api_thread.start()

    def _start_api(self):
        api.pollen_blockchain = self._pollen_blockchain
        api.app.run(debug=False, host="localhost", port=6000)

    def _retrieve_attackers_periodically(self):
        while True:
            try:
                attack_report = self._pollen_blockchain.retrieve_attackers()

                if attack_report:
                    requests.post(self._config['ENDPOINT']['STALK']
                                  + "/api/v1.0/mitigate",
                                  json=json.dumps(
                                          json.loads(
                                              str(attack_report)
                                          )
                                       )
                                  )
                    self._logger.info("Successfully retrieved {} attackers "
                                      "targeting {}"
                                      .format(len(attack_report.addresses),
                                              attack_report.target))
                time.sleep(self._config['INTERVAL']['RETRIEVE_SECONDS'])
            except Exception as e:
                time.sleep(self._config['INTERVAL']['RETRIEVE_SECONDS'])


if __name__ == '__main__':
    BloSS()
