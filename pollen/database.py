from influxdb import InfluxDBClient
from datetime import datetime


class PollenDatabase:
    def __init__(self, config):
        self._config = config
        self._client = InfluxDBClient(self._config['DATABASE']['HOST'],
                                      self._config['DATABASE']['PORT'],
                                      self._config['DATABASE']['USER'],
                                      self._config['DATABASE']['PASSWORD'],
                                      self._config['DATABASE']['NAME'])
        self._client.drop_database(self._config['DATABASE']['NAME'])
        self._client.create_database(self._config['DATABASE']['NAME'])
        # Only keep data for 1 day
        self._client.create_retention_policy(name="drop",
                                             duration="1d",
                                             replication="1",
                                             database=self._config['DATABASE']
                                                                  ['NAME'])

    def _write(self, json_body):
        try:
            self._client.write_points(json_body)
        except:
            pass

    def update_inbound_traffic(self, datapath_id, workload):
        json_body = [
            {
                "measurement": "inboundtraffic",
                "tags":
                    {
                        "datapath_id": datapath_id
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "mbps": workload
                    }
            }
        ]
        self._write(json_body)

    def update_outbound_traffic(self, datapath_id, workload):
        json_body = [
            {
                "measurement": "outboundtraffic",
                "tags":
                    {
                        "datapath_id": datapath_id
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "mbps": workload
                    }
            }
        ]
        self._write(json_body)

    def update_transit_traffic(self, datapath_id, workload):
        json_body = [
            {
                "measurement": "transittraffic",
                "tags":
                    {
                        "datapath_id": datapath_id
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "mbps": workload
                    }
            }
        ]
        self._write(json_body)

    def update_outbound_intratraffic(self, host, ip_address, workload):
        json_body = [
            {
                "measurement": "outboundintratraffic",
                "tags":
                    {
                        "ip_address": ip_address
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "host": host,
                        "mbps": workload

                    }
            }
        ]
        self._write(json_body)

    def update_inbound_intratraffic(host, ip_address, workload):
        "Outbound traffic"
        json_body = [
            {
                "measurement": "inboundintratraffic",
                "tags":
                    {
                        "ip_address": ip_address
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "host": host,
                        "mbps": workload
                    }
            }
        ]
        self._write(json_body)

    def update_reported_addresses(self, datapath_id, count):
        json_body = [
            {
                "measurement": "reported_addresses",
                "tags":
                    {
                        "datapath_id": datapath_id
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "count": count
                    }
            }
        ]
        self._write(json_body)

    def update_blocked_addresses(self, datapath_id, count):
        json_body = [
            {
                "measurement": "blocked_addresses",
                "tags":
                    {
                        "datapath_id": datapath_id
                    },
                "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields":
                    {
                        "count": count
                    }
            }
        ]
        self._write(json_body)