import logging
import os
from configuration import Configuration


class Logger:
    def __init__(self, name):
        self._config = Configuration()
        name_without_spaces = name.replace(' ', '')
        self._log_formatter = logging.Formatter(
            self._config['LOG']['FORMAT'],
            self._config['DEFAULT']['TIMESTAMP_FORMAT']
        )
        file_handler = logging.FileHandler(
            os.path.join(self._config['LOG']['PATH'],
                         name_without_spaces.lower() + ".log"),
            mode='w'
        )
        file_handler.setFormatter(self._log_formatter)
        self._log = logging.getLogger(name_without_spaces)
        log_level = eval(self._config['LOG']['LEVEL'])
        logging.getLogger().setLevel(log_level)
        self._log.setLevel(log_level)
        self._log.addHandler(file_handler)

    def debug(self, message):
        self._log.debug(message)

    def info(self, message):
        self._log.info(message)

    def warning(self, message):
        self._log.warning(message)

    def error(self, message):
        self._log.error(message)

    def critical(self, message):
        self._log.critical(message)
