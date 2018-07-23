import os
import time

from ipfsapi.exceptions import ConnectionError, ProtocolError, TimeoutError
from solc import compile_source
from solc.exceptions import ContractsNotFound
from web3 import Web3, KeepAliveRPCProvider

import paths
from attack_reporting import AttackReporting
from attack_reporting import AttackReportingException
from configuration import Configuration
from datastore import PollenDatastore
from encryption import PollenEncryption
from logger import Logger
from stalk.utils import calculate_subnet


class PollenBlockchain:

    def __init__(self, enable_encryption=True):
        self.config = Configuration()
        self._logger = Logger("Pollen")
        self.attack_reporting = AttackReporting(self.config)
        self._encryption = None
        if enable_encryption:
            self._encryption = PollenEncryption()
        self._datastore = PollenDatastore(
            encryption=self._encryption
        )
        self.web3 = Web3(
            KeepAliveRPCProvider(host=self.config['BLOCKCHAIN']['HOST_ADDRESS'],
                                 port=self.config['BLOCKCHAIN']['PORT']))

        self.account_address = self.web3.eth.accounts[0]
        self.block_gas_limit = self.web3.eth.getBlock(0)["gasLimit"]

        self.web3.personal.unlockAccount(account=self.account_address,
                                         passphrase=self.config['BLOCKCHAIN']
                                         ['ACCOUNT_PASSPHRASE'],
                                         duration=self.config['BLOCKCHAIN']
                                         ['ACCOUNT_UNLOCK_DURATION'])

        relay_contract_filename = (self.config['BLOCKCHAIN']
                                              ['RELAY_SOURCE_FILENAME'])
        relay_contract_address = (self.config['BLOCKCHAIN']
                                             ['RELAY_CONTRACT_ADDRESS'])
        self.relay_contract = self.web3.eth.contract(
            abi=self._compute_contract_abi(relay_contract_filename),
            address=relay_contract_address
        )

        self.system_contract_filename = (self.config['BLOCKCHAIN']
                                                    ['SYSTEM_SOURCE_FILENAME'])
        system_contract_address = (self.config['BLOCKCHAIN']
                                              ['SYSTEM_CONTRACT_ADDRESS'])
        if system_contract_address is not None:
            self.system_contract = self.web3.eth.contract(
                abi=self._compute_contract_abi(self.system_contract_filename),
                address=system_contract_address
            )
        else:
            self.system_contract = self._create_mitigation_contract()
        if self._encryption is not None:
            self.set_public_key(self._encryption.get_serialized_public_key())

    def _load_and_compile_contract(self, contract_source_filename):
        contract_source_path = os.path.join(paths.ROOT_DIR,
                                            'pollen',
                                            contract_source_filename)
        if os.path.exists(contract_source_path):
            with open(contract_source_path, 'r') as f:
                try:
                    contract_source_code = f.read()
                    return compile_source(contract_source_code)
                except (ValueError, ContractsNotFound) as e:
                    self._logger.error("Unable to compile contract source code")
                    return None
        return None

    def _create_mitigation_contract(self):
        compiled = self._load_and_compile_contract(self.system_contract_filename)
        if compiled is not None:
            contract_key = compiled.keys()[0]

            system_contract = self.web3.eth.contract(
                abi=compiled[contract_key]['abi'],
                bytecode=compiled[contract_key]['bin'],
                bytecode_runtime=compiled[contract_key]['bin-runtime'],
            )
            try:
                trans_hash = system_contract.deploy(
                    transaction=self._transact_with_gas()
                )
            except ValueError:
                self._logger.error("Failed deploying autonomous system contract")
                return None
            for _ in range(1, 10):
                trans_receipt = self.web3.eth.getTransactionReceipt(trans_hash)
                if trans_receipt is not None:
                    contract_address = trans_receipt['contractAddress']
                    self.config.set('BLOCKCHAIN', 'SYSTEM_CONTRACT_ADDRESS',
                                    contract_address)
                    self._register_contract_with_relay(contract_address)
                    return system_contract(contract_address)
                time.sleep(2)
        return None

    def _compute_contract_abi(self, contract_filename):
        compiled = self._load_and_compile_contract(contract_filename)
        return compiled[compiled.keys()[0]]['abi']

    def _register_contract_with_relay(self, contract_address):
        subnetworks = self.config['NETWORK']['SUBNETWORKS']
        for subnetwork in subnetworks:
            try:
                tx_hash = (self.relay_contract
                           .transact(self._transact_with_gas())
                           .addSubnetwork(subnetwork, contract_address))
                tx_receipt = self.web3.eth.getTransactionReceipt(tx_hash)
                if tx_receipt is not None:
                    self._logger.info("Associated network {} with contract {}"
                                      .format(subnetwork, contract_address))
            except:
                self._logger.error("Failed to associate subnetwork")

    def _transact_with_gas(self, gas=None):
        if type(gas) is int and 1 <= gas <= self.block_gas_limit:
            return {'from': self.account_address, 'gas': gas}
        return {'from': self.account_address, 'gas': 4700000}

    def set_public_key(self, serialized_public_key):
        try:
            ipfs_hash = self._datastore.store(data=serialized_public_key)
            (self.system_contract
             .transact(self._transact_with_gas())
             .setPublicKey(str(ipfs_hash)))
        except:
            self._logger.error("Failed to publish the RSA public key.")

    def get_public_key_for_subnetwork(self, subnetwork):
        try:
            ipfs_hash = str(self.relay_contract.call(
                {'from': self.account_address,
                 'to': self.relay_contract.address})
                          .getPublicKey(str(subnetwork)))
            if type(ipfs_hash) is str:
                return str(self._datastore.retrieve(ipfs_hash))
        except:
            self._logger.error("Failed to retrieve public key for subdomain {}"
                               .format(subnetwork))

    def set_blocked(self, attack_report_hash, blocked=True):
        try:
            if not self._is_blocked(attack_report_hash):
                tx_hash = (self.system_contract
                           .transact(self._transact_with_gas())
                           .setBlocked(str(attack_report_hash), blocked))
                for _ in range(1, 3):
                    tx_receipt = self.web3.eth.getTransactionReceipt(tx_hash)
                    if tx_receipt is not None:
                        self._logger.info("Blocked attack report with hash {}"
                                          .format(str(attack_report_hash)))
                        return
                    time.sleep(1)
        except:
            self._logger.error("Can't set hash to blocked on blockchain")
        return

    def _is_blocked(self, attack_report_hash):
        try:
            message = str(self.system_contract.call(
                {'from': self.account_address,
                 'to': self.system_contract.address})
                          .isBlocked(str(attack_report_hash)))
            if not message:
                return
            return message.lower() == "true"
        except:
            self._logger.error("Can't get blocking state of hash")
        return

    def _is_valid(self, attack_report_message):
        try:
            # Fallback for unencrypted attack reports
            if "signature" not in attack_report_message:
                return True
            serialized_public_key = self.get_public_key_for_subnetwork(
                calculate_subnet(attack_report_message['target'],
                                 "255.255.255.0")
            )
            return self._encryption.verify(attack_report_message['hash'],
                                           attack_report_message['signature'],
                                           serialized_public_key)
        except:
            return False

    def report_attackers(self, attack_reports):
        try:
            attack_reports = self.attack_reporting.process(attack_reports)

            for attack_report in attack_reports:
                self._logger.info(
                    "Reported {} targeting {}, action: {}, hash: {}, on: {}"
                    .format(attack_report.addresses,
                            attack_report.target,
                            attack_report.action,
                            hash(attack_report),
                            attack_report.timestamp))
                serialized_public_key = self.get_public_key_for_subnetwork(
                    attack_report.subnetwork)
                ipfs_hash = self._datastore.store(
                    data=str(attack_report),
                    to_sign=hash(attack_report),
                    serialized_public_key=serialized_public_key)
                (self.relay_contract
                 .transact(self._transact_with_gas())
                 .reportAttackers(attack_report.subnetwork, ipfs_hash))

        except AttackReportingException as exception:
            self._logger.debug(exception.message)
        return

    def retrieve_attackers(self):
        ipfs_hash = str(self.system_contract.call(
            {'from': self.account_address,
             'to': self.system_contract.address}
        ).retrieveAttackers())
        if not ipfs_hash:
            return
        try:
            message = self._datastore.retrieve(ipfs_hash)
        except (ConnectionError, ProtocolError, TimeoutError) as e:
            self._logger.error("IPFS retrieve of AttackReport failed with {}"
                               .format(str(e)))
            return
        if self._is_valid(message):
            attack_report = (self.attack_reporting
                             .parse_attack_report_message(message))

            if attack_report and not self._is_blocked(hash(attack_report)):

                self._logger.debug("Retrieved IPs {} targeting {} on {}, to {}"
                                   .format(attack_report.addresses,
                                           attack_report.target,
                                           attack_report.timestamp,
                                           attack_report.action))

                return attack_report
        return None
