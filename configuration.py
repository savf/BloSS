import ConfigParser
import json

config = ConfigParser.ConfigParser()
config.read("config.ini")


def get(section, option):
    try:
        json.loads(config.get(section, option))
    except:
        return config.get(section, option)
    return json.loads(config.get(section, option))