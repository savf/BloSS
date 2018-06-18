import ConfigParser
import os
import unittest

import mock

import paths
from configuration import Configuration
from pollen.blockchain import PollenBlockchain


class TestPollenBlockchain(unittest.TestCase):
    @mock.patch('os.path')
    def test_load_and_compile_contract_file_exists(self, mock_path):
        mock_path.exists.return_value = False
        mock_pollen_blockchain = mock.Mock(PollenBlockchain)
        mock_pollen_blockchain.config = Configuration()
        self.assertIsNone(
            PollenBlockchain._load_and_compile_contract(
                mock_pollen_blockchain,
                "../test/test_report.sol"
            )
        )

    def test_load_and_compile_contract_binary(self):
        contract_source_code = ("pragma solidity ^0.4.10;\n" 
                                "\n" 
                                "contract TestReport {\n" 
                                "\n" 
                                "    string helloWorld;\n" 
                                "\n" 
                                "    function TestReport() public\n" 
                                "    {\n" 
                                "        helloWorld = 'Hello World';\n"
                                "    }\n"
                                "}")
        contract_bin = unicode("608060405234801561001057600080fd5b5060408051908"
                               "10160405280600b81526020017f48656c6c6f20576f726c"
                               "64000000000000000000000000000000000000000000815"
                               "2506000908051906020019061005c929190610062565b50"
                               "610107565b8280546001816001161561010002031660029"
                               "00490600052602060002090601f01602090048101928260"
                               "1f106100a357805160ff19168380011785556100d1565b8"
                               "28001600101855582156100d1579182015b828111156100"
                               "d05782518255916020019190600101906100b5565b5b509"
                               "0506100de91906100e2565b5090565b61010491905b8082"
                               "11156101005760008160009055506001016100e8565b509"
                               "0565b90565b6035806101156000396000f3006080604052"
                               "600080fd00a165627a7a723058202fd0e0ffaaf5c883e4f"
                               "2fe45d0baab9a1fb6ae1c321170b44b8186bb016e968e00"
                               "29")
        mock_pollen = mock.Mock(PollenBlockchain)
        mock_pollen.config = Configuration()
        mock_pollen.config.config_parser = ConfigParser.ConfigParser()
        mock_pollen.config.config_parser.read(paths.ROOT_DIR
                                              + "/test/test_config.ini")
        with mock.patch('pollen.blockchain.open',
                        mock.mock_open(read_data=contract_source_code)) as m:
            result = PollenBlockchain._load_and_compile_contract(
                mock_pollen,
                "../test/test_report.sol"
            )
        m.assert_called_once_with(paths.ROOT_DIR
                                  + '/pollen/../test/test_report.sol', 'r')
        # The bytecodes differ on the last 34 bytes (68 characters) due to
        # metadata differences in different versions of the solidity compiler
        self.assertEqual(len(result[result.keys()[0]]['bin']),
                         len(contract_bin))
