from web3 import Web3, KeepAliveRPCProvider
from netaddr import IPNetwork, IPAddress
import input
import ast
import json
import hashlib

from datetime import datetime

'''
Every blockchain-related method will be implemented here
i.e., the 'controller.py' or other modules should not manage
 the 'contract' or the 'web3' API.
'''

global web3, contract, account_address

'''
To keep things up to date we check what is not up to date
'''

global previous_timestamp, previous_attackers

'''
To keep track of hosts retrieved and blocked
'''

global log_blocked_hosts


#TODO: compile/upload the contract here
'''
def create_contract():

    from solc import compile_source

    compiled = compile_source(input.BC_SOURCE_CODE)

    MyContract = web3.eth.contract(
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

'''

def connect():
    '''
    This method should be called as soon as the controller is started, otherwise
    the other methods which interact with the smart contract will fail.
    :return:
    '''

    global web3, contract
    global previous_attackers, previous_timestamp
    global log_blocked_hosts
    global account_address

    previous_timestamp = None #initializing
    previous_attackers = None #initializing
    log_blocked_hosts = {}

    '''
    Create RPC Interface
    '''
    web3 = Web3(KeepAliveRPCProvider(host=input.BC_HOST_ADDRESS, port=input.BC_PORT))

    '''
    Unlock account
    '''
    account_address = web3.eth.accounts[0]
    web3.personal.unlockAccount(account=account_address, passphrase=input.BC_ACCOUNT_PASSWORD,
                                duration=input.BC_ACCOUNT_TIME)
    '''
    Instantiate the contract
    '''

    contract = web3.eth.contract(
        abi=input.BC_CONTRACT_ABI,
        address=input.BC_CONTRACT_ADDRESS
    )

    return True #Yeyy


def set_network(msg):

    '''
    Define the network addresses maintained by an AS in the JSON format
    *msg hardcoded for our example in "input.py" -> BC_AS_NETWORKS
    :param msg: JSON
    :return:
    '''

    global contract, account_address

    try:
        contract.transact(input.transact_with_gas(account_address)).set_network( msg )
    except: #if something goes bad (e.g., contract is not instantiated)
        return None
    return True


def get_network():

    '''
    Retrieve the networks maintained by the different ASEs encoded as JSON

    :return:
    '''

    #TODO: REQUIRE ++TEST/REVIEW

    global contract, account_address
    try:
        network_addr = contract.call( {'from':account_address,'to':contract.address} ).get_network( )
        if network_addr:
            network_addr = json.loads( network_addr )
            #network_addr["ASN1"], network_addr["ASN2"]. network_addr["ASN1"]
            #TODO: we also need to retrieve the contract address of each AS
    except:
        return None
    return True


def report_ipv4(current_attackers):

    '''
    Report bad hosts to the blockchain verifying two conditions:
    1) The previous reported list and the current reported list are different
    2) The fixed interval time to publish addresses should be is respected

    :param current_attackers:
    :return:
    '''

    global contract, account_address
    global previous_timestamp, previous_attackers

    '''
    If the list of 'current_attackers' is empty there is nothing to do
    '''

    if not current_attackers:
        return

    current_timestamp = datetime.now()
    if not previous_timestamp:
        previous_timestamp = current_timestamp
    delta_timestamp_seconds = (current_timestamp - previous_timestamp).seconds

    if delta_timestamp_seconds > input.DEF_IDLE_TIMEOUT:
        previous_attackers = None

    '''
    Fixed time interval to publish addresses. If the list of attackers is not changed in the meanwhile
    '''

    if delta_timestamp_seconds >= input.BC_MIN_REPORT_INTERVAL and delta_timestamp_seconds >= input.BC_MAX_REPORT_INTERVAL:

        #update timestamp
        previous_timestamp = current_timestamp

        '''
        Check the difference in terms of addresses between current and previous 'attackers' list.
        '''

        if not previous_attackers:
            previous_attackers = current_attackers
        # if nothing changed during the time interval, there is nothing to publish
        elif previous_attackers == current_attackers:
            return
        else:
            for issuer, list_addr in current_attackers.iteritems( ):
                for aux_issuer, aux_list_addr in previous_attackers.iteritems():
                    new_attackers = []
                    # update if there is a difference, otherwise do nothing
                    if issuer == aux_issuer:
                        for ip_addr in list_addr:
                            if ip_addr not in aux_list_addr:
                                new_attackers.append(ip_addr)
                        current_attackers[issuer] = new_attackers

            #update list of attackers
            previous_attackers = current_attackers

        # TODO: lookup the networks maintained by each AS and report individually


        for issuer, attackers in current_attackers.iteritems( ):

            #check: if there is nothing to publish, skip iteration
            if not attackers:
                continue



            timestamp = current_timestamp.strftime(input.BC_TIMESTAMP_FORMAT)
            hash = hashlib.sha256(issuer+"blacklist"+timestamp+ "".join(str(i) for i in attackers)).hexdigest()
            body = {
                "issuer": issuer,
                "action": "blacklist",
                "timestamp": timestamp,
                "addresses": attackers,
                "hash": hash
            }


            print ""
            print "*" * 50
            print "REPORTING ADDRESS(ES):"
            print "Timestamp:", timestamp
            print "Issuer:", issuer
            print "Attacker(s):", hash#attackers
            print "Action: blacklist"
            print "Hash:", hash
            print "*" * 50

            tx_hash = contract.transact(input.transact_with_gas(account_address)).report_ipv4(str(body))

    return


def retrieve_ipv4():
    global contract, account_address

    '''
    Check if the contract was created
    '''
    if not contract:
        return

    '''
    Call the smart contract "retrieve_ipv4" method.
    It is a constant method and no "gas" is required.

    - reply is a dictionary
    - require the 'literal_eval' to make the reply python-readable
    - if the reply is empty then there is nothing to retrieve
    '''
    msg = str(contract.call( {'from':account_address, 'to':contract.address} ).retrieve_ipv4( ))

    if not msg:
        return

    try:
        msg = ast.literal_eval(msg)
    except:
        print "Error ast.literal"
        return

    attackers_addresses = []
    attackers_by_issuers = {}
    issuer = None
    action = None
    valid = False

    #log purposes
    delta_ts_by_issuers = {}

    for key, value in msg.iteritems():
        '''
        Check if the message is recent
        '''
        if key == "timestamp":
            msg_timestamp = datetime.strptime(value, input.BC_TIMESTAMP_FORMAT)
            current_timestamp = datetime.now()
            delta_timestamp_seconds = (current_timestamp - msg_timestamp).seconds

            '''
            If the message is old -> ignore it
            '''

            if delta_timestamp_seconds >= input.BC_MAX_RETRIEVE_INTERVAL:
                break
            else:
                valid = True

        elif key == "addresses":
            for ip_addr in value:
                if ip_addr not in attackers_addresses:
                    attackers_addresses.append(ip_addr)

        elif key == "issuer":
            for addr in input.NET1_AS_NETWORK:
                if IPAddress(value) in IPNetwork(addr):
                    issuer = None
                    break
                else:
                    issuer = value
                    break
        elif key == "action":
            action = value

        elif key == "hash":
            hash = value

        #DEBUG
        #try:
        #    print issuer, attackers, valid
        #except:
        #    pass

        if valid and issuer and attackers_addresses and action and hash:
            attackers_by_issuers[issuer] = attackers_addresses
            delta_ts_by_issuers[issuer] = delta_timestamp_seconds

    '''
    Check if 'issuers' has at least 1 report
    And the message was not block-confirmed beforehand
    '''

    global log_blocked_hosts

    if len(attackers_by_issuers) > 0 and hash not in log_blocked_hosts:

        '''
        Include hash in the dict of blocked hosts
        but do not confirm yet
        '''
        log_blocked_hosts = {hash: msg}
        timestamp = current_timestamp.strftime( input.BC_TIMESTAMP_FORMAT )

        print ""
        print "*" * 50
        print "RETRIEVING ADDRESS(ES):"
        print "Timestamp (TS):", timestamp
        print "Delta TS (s):", delta_ts_by_issuers[issuer]
        print "Issuer:", issuer
        print "Attacker(s):", attackers_by_issuers[issuer]
        print "Action: blacklist"
        print "*" * 50

        return hash, attackers_by_issuers
    else:
        return None, None

def confirm_addresses_block(hash_request, attackers):
    global log_blocked_hosts

    #Update self-check
    log_blocked_hosts = {hash_request: attackers}
    timestamp = datetime.now().strftime( input.BC_TIMESTAMP_FORMAT )
    hash_confirm = hashlib.sha256(str(hash_request)+str(timestamp)).hexdigest( )

    print "*" * 50
    print "CONFIRMATION ADDRESS(ES) BLOCKED:"
    print attackers
    print "Timestamp:", timestamp
    print "Hash:", hash_confirm
    print "*" * 50










