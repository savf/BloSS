import ConfigParser
import json

from paths import CONFIG_PATH


class Configuration:
    class OptionFromSection:
        def __init__(self, configuration, section):
            self.configuration = configuration
            self.section = section

        def __getitem__(self, option):
            return self.configuration.get(self.section, option)

    def __init__(self):
        self.config_parser = ConfigParser.ConfigParser()
        self.config_parser.optionxform = str
        self.config_parser.read(CONFIG_PATH)

    def __getitem__(self, section):
        return self.OptionFromSection(self, section)

    def get(self, section, option):
        try:
            return json.loads(self.config_parser.get(section, option, raw=True))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return None
        except ValueError:
            return self.config_parser.get(section, option, raw=True)

    def set(self, section, option, value):
        if not self.config_parser.has_section(section):
            self.config_parser.add_section(section)
        self.config_parser.set(section, option, str(value))

        try:
            with open(CONFIG_PATH, 'w') as f:
                self.config_parser.write(f)
        except:
            pass

