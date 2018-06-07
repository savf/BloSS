import ConfigParser
import unittest
import mock
import paths
from configuration import Configuration


class TestConfiguration(unittest.TestCase):

    def setUp(self):
        self.config = Configuration()
        self.config.config_parser = ConfigParser.ConfigParser()
        self.config.config_parser.read(paths.ROOT_DIR
                                       + "/test/test_config.ini")

    def test_get(self):
        self.assertEqual(self.config.get('SECTIONONE', 'OPTIONONE'),
                         'This is a string')
        self.assertEqual(self.config.get('SECTIONONE', 'OPTIONTWO'),
                         23)
        self.assertEqual(self.config.get('SECTIONONE', 'OPTIONTHREE'),
                         ["item1", "item2", "item3"])
        self.assertEqual(self.config.get('SECTIONONE', 'OPTIONFOUR'),
                         {'key1': "value1", 'key2': "value2"})
        self.assertIsNone(self.config.get('SECTIONONE', 'OPTIONFIVE'))
        self.assertIsNone(self.config.get('SECTIONFIVE', 'OPTIONONE'))
        self.assertIsNone(self.config.get('', ''))
        self.assertIsNone(self.config.get('SECTIONONE', ''))
        self.assertEqual(self.config.get('SECTIONTHREE', 'OPTIONONE'),
                         "0x7cc7a2f1113165a92bb5fb657cac997261211f40")
        self.assertEqual(self.config.get('SECTIONTHREE', 'OPTIONTWO'),
                         "DE:AD:BE:EF:FE:ED")
        self.assertEqual(self.config.get('SECTIONTHREE', 'OPTIONTHREE'),
                         "192.168.0.1")
        self.assertEqual(self.config.get('SECTIONTWO', 'FORMAT'),
                         "%(asctime)s:%(name)s:%(levelname)s:%(message)s")

    def test_itemget(self):
        # self.assertEqual(self.config['SECTIONONE']['OPTIONONE'],
        #                  'This is a string')
        self.assertEqual(self.config['SECTIONONE']['OPTIONTWO'],
                         23)
        self.assertEqual(self.config['SECTIONONE']['OPTIONTHREE'],
                         ["item1", "item2", "item3"])
        self.assertEqual(self.config['SECTIONONE']['OPTIONFOUR'],
                         {'key1': "value1", 'key2': "value2"})
        self.assertIsNone(self.config['SECTIONONE']['OPTIONFIVE'])
        self.assertIsNone(self.config['SECTIONFIVE']['OPTIONONE'])
        self.assertIsNone(self.config[''][''])
        self.assertIsNone(self.config['SECTIONONE'][''])
        self.assertEqual(self.config['SECTIONTHREE']['OPTIONONE'],
                         "0x7cc7a2f1113165a92bb5fb657cac997261211f40")
        self.assertEqual(self.config['SECTIONTHREE']['OPTIONTWO'],
                         "DE:AD:BE:EF:FE:ED")
        self.assertEqual(self.config['SECTIONTHREE']['OPTIONTHREE'],
                         "192.168.0.1")
        self.assertEqual(self.config['SECTIONTWO']['FORMAT'],
                         "%(asctime)s:%(name)s:%(levelname)s:%(message)s")

    def test_set_string(self):
        with mock.patch('configuration.open',
                        mock.mock_open()) as m:
            self.config.set('SECTIONONE', 'OPTIONFIVE', '2342')
        m.assert_called_once_with(paths.CONFIG_PATH, 'w')
        self.assertEqual(self.config['SECTIONONE']['OPTIONFIVE'], 2342)

    def test_set_integer(self):
        with mock.patch('configuration.open',
                        mock.mock_open()) as m:
            self.config.set('SECTIONONE', 'OPTIONFIVE', 2342)
        m.assert_called_once_with(paths.CONFIG_PATH, 'w')
        self.assertEqual(self.config['SECTIONONE']['OPTIONFIVE'], 2342)
