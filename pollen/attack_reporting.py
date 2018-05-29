import json
from datetime import datetime


class AttackReportingException(Exception):
    def __init__(self, message):
        self.message = message

        def __str__(self):
            return repr(self.message)


class AttackReport:
    def __init__(self,
                 target, action, timestamp, addresses,
                 hash=None):
        self._target = target
        self._action = action
        self._timestamp = timestamp
        self._addresses = addresses
        if (hash is None and target is not None
                and action is not None
                and timestamp is not None):
            self._calculate_hash()
        else:
            self._hash = hash

    def __str__(self):
        dict_representation = {"target": self.target,
                               "action": self.action,
                               "timestamp": str(self.timestamp),
                               "addresses": self.addresses,
                               "hash": self._hash}
        return json.dumps(dict_representation)

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        try:
            return (self.target == other.target and
                    self.action == other.action and
                    self.timestamp == other.timestamp and
                    self.addresses == other.addresses)
        except AttributeError:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def _calculate_hash(self):
        self._hash = hash((self.target, self.action, self.timestamp))

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
    def addresses(self):
        return self._addresses

    @addresses.setter
    def addresses(self, value):
        self._addresses = value


class AttackReporting:
    def __init__(self, config):
        self._config = config
        self._last_report_timestamp = None
        self._last_attack_reports_by_target = {}

    def report(self, attack_reports_by_target):
        if not attack_reports_by_target:
            raise AttackReportingException('No attack reports provided.')

        current_timestamp = datetime.now()
        if not self._last_report_timestamp:
            self._last_report_timestamp = current_timestamp
        timespan_since_last_report = (current_timestamp
                                      - self._last_report_timestamp).seconds

        if (timespan_since_last_report
                > self._config['INTERVAL']['MAX_REPORT_SECONDS']):
            self._last_attack_reports_by_target = {}

        if (timespan_since_last_report
                >= self._config['INTERVAL']['MIN_REPORT_SECONDS']):

            self._last_report_timestamp = current_timestamp

            if not self._last_attack_reports_by_target:
                self._last_attack_reports_by_target = attack_reports_by_target
            elif self._last_attack_reports_by_target == attack_reports_by_target:
                return
            else:
                for attack_report in attack_reports_by_target:
                    if attack_report.target in self._last_attack_reports_by_target:
                        target = attack_report.target
                        old_attackers = (
                                set(attack_report.addresses)
                                & set(self._last_attack_reports_by_target[target]
                                      .addresses)
                        )
                        attack_report.addresses = list(
                            set(attack_report.addresses) - old_attackers
                        )

                self._last_attack_reports_by_target = attack_reports_by_target
        return self._last_attack_reports_by_target

    def parse_attack_report_message(self, message):
        message_keys = ["target", "action", "timestamp", "addresses", "hash"]
        if any(key not in message for key in message_keys):
            raise AttackReportingException('Attack report message malformed.')
        target = action = message_timestamp = attackers_addresses = hash = None
        for key, value in message.iteritems():
            if key == "target":
                target = value
            elif key == "action":
                action = value
            elif key == "timestamp":
                message_timestamp = (datetime
                                     .strptime(value,
                                               self._config['DEFAULT']
                                               ['TIMESTAMP_FORMAT']))
                current_timestamp = datetime.now()
                delta_timestamp_seconds = (current_timestamp
                                           - message_timestamp).seconds

                if (delta_timestamp_seconds
                        >= self._config['INTERVAL']
                                       ['MESSAGE_LIFETIME_SECONDS']):
                    return None

            elif key == "addresses":
                attackers_addresses = list(set(value))

            elif key == "hash":
                hash = value

        return AttackReport(target=target,
                            action=action,
                            timestamp=message_timestamp,
                            addresses=attackers_addresses,
                            hash=hash)
