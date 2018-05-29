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
        os.path.exists.return_value = False
        mock_pollen_blockchain = mock.Mock(PollenBlockchain)
        mock_pollen_blockchain.config = Configuration()
        self.assertIsNone(
            PollenBlockchain._load_and_compile_contract(mock_pollen_blockchain))

    def test_load_and_compile_contract_binary(self):
        contract_source_code = "pragma solidity ^0.4.10;" \
                               "" \
                               "contract TestReport {" \
                               "" \
                               "    string helloWorld;" \
                               "" \
                               "    function TestReport() public" \
                               "    {" \
                               "        helloWorld = 'Hello World';" \
                               "    }" \
                               "}"
        contract_bin = unicode("6060604052341561000f57600080fd5b60408051908101"
                               "60405280600b81526020017f48656c6c6f20576f726c64"
                               "0000000000000000000000000000000000000000008152"
                               "506000908051906020019061005a929190610060565b50"
                               "610105565b828054600181600116156101000203166002"
                               "900490600052602060002090601f016020900481019282"
                               "601f106100a157805160ff19168380011785556100cf56"
                               "5b828001600101855582156100cf579182015b82811115"
                               "6100ce5782518255916020019190600101906100b3565b"
                               "5b5090506100dc91906100e0565b5090565b6101029190"
                               "5b808211156100fe5760008160009055506001016100e6"
                               "565b5090565b90565b6035806101136000396000f30060"
                               "60604052600080fd00a165627a7a72305820ac8bc40dd4"
                               "c2561de723540a69723414fc9aa91b4307af6014fe6936"
                               "0b66c1a10029")
        mock_pollen_blockchain = mock.Mock(PollenBlockchain)
        mock_pollen_blockchain.config = Configuration()
        mock_pollen_blockchain.config.config_parser = ConfigParser.ConfigParser()
        mock_pollen_blockchain.config.config_parser.read(paths.ROOT_DIR +
                                                   "/test/test_config.ini")
        mock_pollen_blockchain.config.return_value = 'test_report.sol'
        with mock.patch('pollen.core.open',
                        mock.mock_open(read_data=contract_source_code)) as m:
            result = PollenBlockchain._load_and_compile_contract(mock_pollen_blockchain)
        m.assert_called_once_with('test_report.sol', 'r')
        # TODO: Binary is NOT platform- or compiler- independent, so this is
        #       no long-term solution, replace with independent test
        self.assertEqual(result[result.keys()[0]]['bin'], contract_bin)
