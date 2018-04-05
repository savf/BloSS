#!/bin/sh

#Source
#https://hackernoon.com/setup-your-own-private-proof-of-authority-ethereum-network-with-geth-9a0a3750cda8

#Proof-of-Authority

#Genesis file: genesis.json
#ChainID or --networkid is configured as '20'


#Unlock accounts if needed
#personal.unlockAccount(eth.accounts[0], "123456", 999999)


#tkb14 or 192.168.30.14
geth --syncmode 'fast' --rpc --rpcapi 'personal,db,eth,net,web3,admin' --rpcaddr 0.0.0.0 --bootnodes 'enode://8a5dd3ed2eb02089f5b7397fc0c6f05f9335de1eda975ee83b51d3d07f4b31dcc165d0fe144ea3e0567be158cf819576e713e143afe2339474651ff9372125bb@[192.168.10.2]:30310' --networkid 20 console --unlock '0xd43362f066e3710886be941488ee4cf1619b938d' --password /home/ethereum/wallet_passphrase
