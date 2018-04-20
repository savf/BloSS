import ConfigParser
import json


class Configuration:
    class OptionFromSection:
        def __init__(self, configuration, section):
            self.configuration = configuration
            self.section = section

        def __getitem__(self, option):
            return self.configuration.get(self.section, option)

    def __init__(self):
        self.config_parser = ConfigParser.ConfigParser()
        self.config_parser.read("config.ini")

    def __getitem__(self, section):
        return self.OptionFromSection(self, section)

    def get(self, section, option):
        try:
            json.loads(self.config_parser.get(section, option))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None
        except ValueError:
            return self.config_parser.get(section, option)
        return json.loads(self.config_parser.get(section, option))