import ipfsapi

"""
This module provides methods for adding and receiving files over IPFS and add peers to the swarm.
"""
# Declare the connection parameters to the IPFS gateway
ipfs_host = 'localhost'
ipfs_port = 5001


def ipfs_add(fileName):
    """
    Writes the list of attackers to the IPFS as JSON.

    Establishes a connection to ipfs by a given gateway. Converts the list to JSON and publishes the list to IPFS.

    @param current_attackers: A dictionary containing IPv4 addresses
    @return: A hash value representing the file stored on IPFS
    """
    global ipfs_host
    global ipfs_port
    connection = ipfsapi.connect(ipfs_host, ipfs_port)

    # add file to ipfs
    res = connection.add(fileName)

    return res['Hash']


def ipfs_get(hash):
    """
    Gets a file from IPFS and converts it to a dictionary.

    :param hash: a valid hash value under which a file is stored in IPFS
    :return: dictionary containing the ip addresses from the file
    """
    global ipfs_host
    global ipfs_port
    connection = ipfsapi.connect(ipfs_host, ipfs_port)

    ipfs_file = connection.cat(hash)

    # return json.loads(ipfs_file)
    return ipfs_file


def ipfs_swarm(addr):
    """
    Adds a peer to the IPFS swarm.

    :param addr: IPFS multiaddress (String)
    :return: boolean
    """
    global ipfs_host
    global ipfs_port

    connection = ipfsapi.connect(ipfs_host, ipfs_port)
    return connection.swarm_connect(addr)
