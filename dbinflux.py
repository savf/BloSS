'''
Import InfluxDB and create identity to write a timeseries
'''

from influxdb import InfluxDBClient
from datetime import datetime
import input

client = InfluxDBClient( input.DB_HOST, input.DB_PORT, input.DB_USER, input.DB_PASSWORD, input.DB_NAME )
#Drop database and create a new one
client.drop_database(input.DB_NAME)
client.create_database(input.DB_NAME)
client.create_retention_policy(name="drop", duration="1d", replication= "1", database=input.DB_NAME)

current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def write(json_body):
    try:
        client.write_points(json_body)
    except:
        pass

'''
Write in InfluxDB timeseries
'''
def update_inbound_traffic(dpid, workload):
    "Inbound traffic"
    json_body = [
        {
            "measurement": "inboundtraffic",
            "tags":
            {
                "dpid": dpid
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
            {
                "mbps": workload
            }
        }
    ]
    write(json_body)

def update_outbound_traffic(dpid, workload):
    "Outbound traffic"
    json_body = [
        {
            "measurement": "outboundtraffic",
            "tags":
            {
                "dpid": dpid
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
            {
                "mbps": workload
            }
        }
    ]
    write(json_body)

def update_transit_traffic(dpid, workload):
    "Transit traffic"
    json_body = [
        {
            "measurement": "transittraffic",
            "tags":
                {
                    "dpid": dpid
                },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
                {
                    "mbps": workload
                }
        }
    ]
    write(json_body)

def update_outbound_intratraffic(host, ip_addr, workload):
    "Outbound traffic"
    json_body = [
        {
            "measurement": "outboundintratraffic",
            "tags":
            {
                "ip_addr": ip_addr
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
            {
                "host": host,
                "mbps": workload

            }
        }
    ]
    write(json_body)

def update_inbound_intratraffic(host, ip_addr, workload):
    "Outbound traffic"
    json_body = [
        {
            "measurement": "inboundintratraffic",
            "tags":
            {
                "ip_addr": ip_addr
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
            {
                "host": host,
                "mbps": workload
            }
        }
    ]
    write(json_body)

def update_reported_addr(dpid, count):
    "reported"
    json_body = [
        {
            "measurement": "reported_addresses",
            "tags":
            {
                "dpid": dpid
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
            {
                "count": count
            }
        }
    ]
    write(json_body)

def update_blocked_addr(dpid, count):
    "blocked"
    json_body = [
        {
            "measurement": "blocked_addresses",
            "tags":
                {
                    "dpid": dpid
                },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "fields":
                {
                    "count": count
                }
        }
    ]
    write(json_body)