from netaddr import IPNetwork, IPAddress


def calculate_subnet(ip_address, netmask):
    netmask_bits = str(IPAddress(netmask).netmask_bits())
    return str(IPNetwork(ip_address + "/" + netmask_bits).cidr)


def safedivision(dividend, divisor):
    return dividend / max(1.0, divisor)
