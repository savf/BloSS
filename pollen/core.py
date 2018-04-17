from web3 import Web3, KeepAliveRPCProvider
from netaddr import IPNetwork, IPAddress
import input
import ast
import json
import hashlib
import ConfigParser

from datetime import datetime


config = ConfigParser.ConfigParser()
config.read("../config.ini")


class PollenCore:

    def __init__(self):
        # TODO: What are these timestamps for?
        previous_timestamp = None  # initializing
        previous_attackers = None  # initializing
        log_blocked_hosts = {}

        self.web3 = Web3(KeepAliveRPCProvider(host=input.BC_HOST_ADDRESS, port=input.BC_PORT))

        '''
        Unlock account
        '''
        self.account_address = self.web3.eth.accounts[0]
        self.web3.personal.unlockAccount(account=self.account_address, passphrase=input.BC_ACCOUNT_PASSWORD,
                                         duration=input.BC_ACCOUNT_TIME)
        '''
        Instantiate the contract
        '''

        contract = web3.eth.contract(
            abi=input.BC_CONTRACT_ABI,
            address=input.BC_CONTRACT_ADDRESS
        )


    #TODO: compile/upload the contract here
    def create_mitigation_contract(self):
        from solc import compile_source

        compiled = compile_source(input.BC_SOURCE_CODE)

        myContract = web3.eth.contract(
            abi = compiled['<stdin>:MyToken']['abi'],
            bytecode = compiled['<stdin>:MyToken']['bin'],
            bytecode_runtime = compiled['<stdin>:MyToken']['bin-runtime'],
        )

        trans_hash = MyContract.deploy(transaction={'from':web3.eth.accounts[0],'value':120})
        # Wait for mining
        trans_receipt = web3.eth.getTransactionReceipt(trans_hash)

        # Get the contract address
        contract_address = trans_receipt['contractAddress']

        # Instantiate the contract factory to get an instance of the contract.
        my_contract = MyContract(contract_address)
