pragma solidity ^0.4.10;

contract AutonomousSystem {

    string storedData;
    string network;
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

    function setNetwork(string network_) {
        network = network_;
    }

    function getNetwork() constant returns (string) {
        return network;
    }

    function reportAttackers(string attackReport_) {
        storedData = attackReport_;
    }

    function setBlocked(string hash_)
        onlyBy(owner)
    {
        blockedAttackers[hash_] = true;
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