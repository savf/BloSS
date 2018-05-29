pragma solidity ^0.4.10;

contract SimpleReport {

    string storedData;
    string network;
    address public owner;

    function set_network(string x){
        network = x;
    }

    function get_network() constant returns (string) {
        return network;
    }

    function report_attackers(string x) {
        storedData = x;
    }

    function retrieve_attackers() constant returns (string) {
        return storedData;
    }
}