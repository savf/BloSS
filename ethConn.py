from web3 import Web3, HTTPProvider, TestRPCProvider
from solc import compile_source
from web3.contract import ConciseContract
import time
import io

"""
This module provides access to an Ethereum blockchain using an geth client.
This module allows to complie and deploy a contract for an off-chain storage solution using IPFS 
amd interacting with this contract.
Connection parameters to a geth client have to get adjusted in the file.
"""

# Geth IP-address
geth_ip = '127.0.0.1'
# Geth port
geth_port = '8545'
# Ethereum account password
geth_password = "Account Password"

# Define connection details
w3 = Web3(HTTPProvider('http://' + geth_ip + ':' + geth_port))
# Unlock the ethereum accout for performing transactions
w3.personal.unlockAccount(w3.eth.accounts[0], geth_password, 0)

# Smart Contract code in Solidity
contract_source_code = '''
pragma solidity ^0.4.0;

contract Offchain {
    address owner;
    string public ipfsHash;
    string public sendTime;
    string public ipfsAddress;

    function Offchain() {
        ipfsHash = 'initialHash';
        sendTime = 'initialTime';
        ipfsAddress = 'initial';
        owner = msg.sender;
    }

    function setHash(string _hash, string _time) public {
        ipfsHash = _hash;
        sendTime = _time;
    }

    function getHash() constant returns (string) {
        return ipfsHash;
    }  

    function getSendTime() constant returns (string) {
        return sendTime;
    }  
    
    function setIPFSAddress(string _addr) public {
        ipfsAddress = _addr;
    }

    function getIPFSAddress() constant returns (string) {
        return ipfsAddress;
    }
}
'''

# Compile smart contract
compiled_sol = compile_source(contract_source_code)
contract_interface = compiled_sol['<stdin>:Offchain']
# Instantiate and deploy contract
contract = w3.eth.contract(contract_interface['abi'], bytecode=contract_interface['bin'])


def deploy_contract():
    """
    Deploys the smart contract to the blockchain.

    Deploys the contract and saves the contract address in a textfile 'own.config'
    :return: contract address
    """
    hash = contract.deploy(transaction={'from': w3.eth.accounts[0], 'gas': 999999})
    file = io.open('own.config', 'w')
    file.write(hash)
    file.close()
    return hash


def connect_bc(hash):
    """
    Connect to a smart contract on the blockchain.

    :param hash: hash value of a contract
    :return: connection to geth
    """
    # Get tx receipt for getting the contract address
    tx_receipt = w3.eth.getTransactionReceipt(hash)
    contract_address = tx_receipt['contractAddress']

    # Return contract instance
    return w3.eth.contract(contract_interface['abi'], contract_address, ContractFactoryClass=ConciseContract)


def get_ipfs_hash(txHash):
    """
    Get the IPFS hash value out of a smart contract.

    :param txHash: address of the smart contract
    :return: an IPFS hash value
    """
    return connect_bc(txHash).getHash()


def get_ipfs_time(txHash):
    """
    Get the time when the contract was updated with a new IPFS hash value.

    :param txHash: address of the smart contract
    :return: timestamp (default is 0.0)
    """
    value = connect_bc(txHash).getSendTime()
    if value != 'initialTime':
        return float(value)
    else:
        return 0.0


def set_ipfs_hash(txHash, ipfsHash):
    """
    Update a smart contract with a new IPFS hash.

    Sets also the time value of the contract to the actual time.
    :param txHash: address of the smart contract to update
    :param ipfsHash: IPFS hash value to instert into the contract
    :return:
    """
    return connect_bc(txHash).setHash(ipfsHash, str(time.time()), transact={'from': w3.eth.accounts[0]})


def get_ipfs_address(txHash):
    """
    Returns the IPFS multiaddress of the contract owner.

    :param txHash: address of a smart contract
    :return: IPFS multiaddress (default False if no address is available)
    """
    value = connect_bc(txHash).getIPFSAddress()
    # Check for default value
    if value != 'initial':
        return value
    else:
        return False


def set_ipfs_address(txHash, ipfsAddress):
    """
    Sets the own multiaddress of IPFS to the smart contract.

    :param txHash: address of the own smart contract
    :param ipfsAddress: IPFS multiaddress
    :return: boolean for success
    """
    return connect_bc(txHash).setIPFSAddress(ipfsAddress, transact={'from': w3.eth.accounts[0]})


def get_own_contract():
    """
    Returns the hash of the own smart contract.

    :return: hash value
    """
    file = io.open('own.config', 'r')
    hash = file.read().replace('\n', '')
    file.close()
    return hash


def get_contracts():
    """
    Returns a list of smart contracts from BloSS instances.

    :return: list of hash values
    """
    hash = []
    file = io.open('contracts.config', 'r')
    for line in file:
        hash.append(line.replace('\n', ''))
    file.close()
    return hash
