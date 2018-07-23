import datetime
import unittest

from pollen.attack_reporting import AttackReport


class TestAttackReporting(unittest.TestCase):
    def setUp(self):
        pass

    def test_attack_report_equality(self):
        timestamp = datetime.datetime.now()
        subnetwork = "192.168.20.0/24"
        addresses = ["192.168.20.1", "192.168.20.2", "192.168.20.3"]
        report_one = AttackReport("192.168.10.1", "blackhole",
                                  timestamp, subnetwork, addresses)
        report_two = AttackReport("192.168.10.1", "blackhole",
                                  timestamp, subnetwork, addresses)
        self.assertTrue(report_one == report_two)
