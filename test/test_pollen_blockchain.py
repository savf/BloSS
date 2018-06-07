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
            PollenBlockchain._load_and_compile_contract(mock_pollen_blockchain))

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
        contract_bin = unicode("6060604052341561000f57600080fd5b604080519081016"
                               "0405280600b81526020017f48656c6c6f20576f726c6400"
                               "00000000000000000000000000000000000000008152506"
                               "000908051906020019061005a929190610060565b506101"
                               "05565b82805460018160011615610100020316600290049"
                               "0600052602060002090601f016020900481019282601f10"
                               "6100a157805160ff19168380011785556100cf565b82800"
                               "1600101855582156100cf579182015b828111156100ce57"
                               "82518255916020019190600101906100b3565b5b5090506"
                               "100dc91906100e0565b5090565b61010291905b80821115"
                               "6100fe5760008160009055506001016100e6565b5090565"
                               "b90565b6035806101136000396000f30060606040526000"
                               "80fd00a165627a7a72305820ac8bc40dd4c2561de723540"
                               "a69723414fc9aa91b4307af6014fe69360b66c1a10029")
        mock_pollen = mock.Mock(PollenBlockchain)
        mock_pollen.config = Configuration()
        mock_pollen.config.config_parser = ConfigParser.ConfigParser()
        mock_pollen.config.config_parser.read(paths.ROOT_DIR
                                              + "/test/test_config.ini")
        with mock.patch('pollen.blockchain.open',
                        mock.mock_open(read_data=contract_source_code)) as m:
            result = PollenBlockchain._load_and_compile_contract(mock_pollen)
        m.assert_called_once_with(paths.ROOT_DIR
                                  + '/pollen/../test/test_report.sol', 'r')
        # The bytecodes differ on the last 34 bytes (68 characters) due to
        # metadata differences in different versions of the solidity compiler
        self.assertEqual(len(result[result.keys()[0]]['bin']),
                         len(contract_bin))
