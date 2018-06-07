import json
from datetime import datetime


class AttackReportingException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return repr(self.message)


class AttackReport(object):
    def __init__(self, target, action, timestamp,
                 subnetwork, addresses, hash=None):
        self._target = self.target = target
        self._action = self.action = action
        self._timestamp = self.timestamp = timestamp
        self._subnetwork = self.subnetwork = subnetwork
        self._addresses = self.addresses = addresses
        if (hash is None and target is not None
                and action is not None
                and timestamp is not None):
            self._calculate_hash()
        else:
            self._hash = hash

    def __str__(self):
        dict_representation = {"target": self.target,
                               "action": self.action,
                               "timestamp": self.timestamp,
                               "subnetwork": self.subnetwork,
                               "addresses": list(self.addresses),
                               "hash": self._hash}
        return json.dumps(dict_representation)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        try:
            return (self.target == other.target and
                    self.action == other.action and
                    self.timestamp == other.timestamp and
                    self.subnetwork == other.subnetwork and
                    self.addresses == other.addresses)
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def _calculate_hash(self):
        self._hash = hash((self.target,
                           self.action,
                           self.subnetwork,
                           self.timestamp))

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._action = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        self._timestamp = value

    @property
    def subnetwork(self):
        return self._subnetwork

    @subnetwork.setter
    def subnetwork(self, value):
        self._subnetwork = value

    @property
    def addresses(self):
        return self._addresses

    @addresses.setter
    def addresses(self, value):
        self._addresses = value


class AttackReporting:
    def __init__(self, config):
        self._config = config
        self._last_report_timestamp = datetime.now()
        self._last_attack_reports = []

    def process(self, attack_reports):
        if not attack_reports:
            raise AttackReportingException('No attack reports provided.')

        current_timestamp = datetime.now()
        timespan_since_last_report = (current_timestamp
                                      - self._last_report_timestamp).seconds

        max_interval = self._config['INTERVAL']['MAX_REPORT_SECONDS']
        min_interval = self._config['INTERVAL']['MIN_REPORT_SECONDS']

        if timespan_since_last_report > max_interval:
            self._last_attack_reports = []

        if timespan_since_last_report >= min_interval:
            self._last_report_timestamp = current_timestamp

            if not self._last_attack_reports:
                self._last_attack_reports = attack_reports
            elif self._last_attack_reports == attack_reports:
                raise AttackReportingException('Reports already submitted.')
            else:
                for report in attack_reports:
                    for last_report in self._last_attack_reports:
                        if (report.target == last_report.target and
                                report.subnetwork == last_report.subnetwork):
                            old_attackers = (report.addresses
                                             & last_report.addresses)
                            report.addresses = (report.addresses
                                                - old_attackers)

                self._last_attack_reports = attack_reports
        else:
            raise AttackReportingException('Reporting frequency too high.')
        return self._last_attack_reports

    def parse_attack_report_message(self, message):
        message_keys = ["target", "action", "timestamp",
                        "subnetwork", "addresses", "hash"]
        if any(key not in message for key in message_keys):
            raise AttackReportingException('Attack report message malformed.')
        timestamp_format = self._config['DEFAULT']['TIMESTAMP_FORMAT']
        target = action = timestamp = subnetwork = addresses = hash = None
        for key, value in message.iteritems():
            if key == "target":
                target = value
            elif key == "action":
                action = value
            elif key == "timestamp":
                timestamp = datetime.strptime(value, timestamp_format)
                current_timestamp = datetime.now()
                delta_timestamp_seconds = (current_timestamp
                                           - timestamp).total_seconds()
                if (delta_timestamp_seconds
                        >= self._config['INTERVAL']
                                       ['MESSAGE_LIFETIME_SECONDS']):
                    return None
            elif key == "subnetwork":
                subnetwork = str(value)
            elif key == "addresses":
                addresses = set(value)

            elif key == "hash":
                hash = value

        return AttackReport(target=target,
                            action=action,
                            timestamp=timestamp.strftime(timestamp_format),
                            subnetwork=subnetwork,
                            addresses=addresses,
                            hash=hash)
