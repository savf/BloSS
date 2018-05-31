import ast
import json
import os
import time

from solc import compile_source
from solc.exceptions import ContractsNotFound
from web3 import Web3, KeepAliveRPCProvider

import paths
from attack_reporting import AttackReporting
from attack_reporting import AttackReportingException
from configuration import Configuration
from logger import Logger


class PollenBlockchain:

    def __init__(self):
        self.config = Configuration()
        self._logger = Logger("Pollen")
        self.attack_reporting = AttackReporting(self.config)

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

        contract_address = self.config['BLOCKCHAIN']['CONTRACT_ADDRESS']
        if contract_address is not None:

            self.contract = self.web3.eth.contract(
                abi=self._compute_contract_abi(),
                address=contract_address
            )
        else:
            self.contract = self._create_mitigation_contract()

    def _load_and_compile_contract(self):
        contract_source_path = os.path.join(paths.ROOT_DIR,
                                            'pollen',
                                            self.config['BLOCKCHAIN']
                                            ['CONTRACT_SOURCE_FILENAME'])
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
        compiled = self._load_and_compile_contract()
        if compiled is not None:
            contract_key = compiled.keys()[0]
            mitigation_contract = self.web3.eth.contract(
                abi=compiled[contract_key]['abi'],
                bytecode=compiled[contract_key]['bin'],
                bytecode_runtime=compiled[contract_key]['bin-runtime'],
            )
            try:
                trans_hash = mitigation_contract.deploy(
                    transaction={'from': self.web3.eth.accounts[0],
                                 'gas': 500000})
            except ValueError:
                self._logger.error("Failed to deploy mitigation contract")
                return None
            for _ in range(1, 10):
                trans_receipt = self.web3.eth.getTransactionReceipt(trans_hash)
                if trans_receipt is not None:
                    contract_address = trans_receipt['contractAddress']
                    self.config.set('BLOCKCHAIN', 'CONTRACT_ADDRESS',
                                    contract_address)
                    return mitigation_contract(contract_address)
                time.sleep(1)
        return None

    def _compute_contract_abi(self):
        compiled = self._load_and_compile_contract()
        return compiled[compiled.keys()[0]]['abi']

    def _transact_with_gas(self, gas=None):
        if type(gas) is int and 1 <= gas <= self.block_gas_limit:
            return {'from': self.account_address, 'gas': gas}
        return {'from': self.account_address, 'gas': 4700000}

    def set_network(self, message):
        try:
            (self.contract
             .transact(self._transact_with_gas())
             .set_network(message))
        except:
            self._logger.error("Unable to store addresses in blockchain")
            return False
        return True

    def get_network(self):
        # TODO: This is not implemented in the contract,
        # see https://trello.com/c/9uXAGl7y
        try:
            network_address = (self.contract
                               .call({'from': self.account_address,
                                      'to': self.contract.address})
                               .get_network())
            if network_address:
                network_address = json.loads(network_address)
        except:
            self._logger.error("Can't access network addresses from blockchain")
            return None
        return True

    def report_attackers(self, attack_reports_by_target):
        try:
            attack_reports = (self.attack_reporting
                              .report(attack_reports_by_target))

            for attack_report in attack_reports:
                self._logger.debug(
                    "Reported {} targeting {}, action: {}, hash: {}, on: {}"
                    .format(attack_report.addresses,
                            attack_report.target,
                            attack_report.action,
                            attack_report.hash,
                            attack_report.timestamp))

                tx_hash = (self.contract
                           .transact(self._transact_with_gas())
                           .report_attackers(str(attack_report)))
                tx_receipt = self.web3.eth.getTransactionReceipt(tx_hash)
                if tx_receipt is not None:
                    self._logger.info("Attackers have been reported in block {}"
                                      .format(tx_receipt['blockNumber']))

        except AttackReportingException:
            self._logger.error("List of attack reports empty or no list given")
            pass
        return

    def retrieve_attackers(self):
        message = str(self.contract.call(
            {'from': self.account_address,
             'to': self.contract.address})
                      .retrieve_attackers())
        if not message:
            return
        try:
            message = ast.literal_eval(message)
        except ValueError:
            self._logger.error("Message malformed, AST literal eval impossible")
            return
        attack_report = (self.attack_reporting
                         .parse_attack_report_message(message))

        self._logger.debug("Retrieved IPs {} targeting {} on {}, action {}"
                           .format(attack_report.addresses,
                                   attack_report.target,
                                   attack_report.timestamp,
                                   attack_report.action))

        return attack_report
