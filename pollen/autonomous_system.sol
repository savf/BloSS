pragma solidity ^0.4.10;

contract AutonomousSystem {

    string storedData;
    string publicKey;
    address public owner = msg.sender;
    mapping(string => bool) blockedAttackers;

    modifier onlyBy(address account_)
    {
        require(
            msg.sender == account_
        );
        // Do not forget the "_;"! It will
        // be replaced by the actual function
        // body when the modifier is used.
        _;
    }

    function setPublicKey(string ipfsHash_)
        onlyBy(owner)
    {
        publicKey = ipfsHash_;
    }

    function getPublicKey() constant returns (string) {
        return publicKey;
    }

    function reportAttackers(string attackReport_) {
        storedData = attackReport_;
    }

    function setBlocked(string hash_, bool blocked_)
        onlyBy(owner)
    {
        blockedAttackers[hash_] = blocked_;
    }

    function isBlocked(string hash_) constant returns (bool) {
        return blockedAttackers[hash_];
    }

    function retrieveAttackers()
        constant
        onlyBy(owner)
        returns (string)
    {
        return storedData;
    }
}