import logging
import configparser
import os

log = logging.getLogger(__name__)
_thangs_config = None


def get_config():
    global _thangs_config
    return _thangs_config


def initialize(version):
    global _thangs_config
    _thangs_config = ThangsConfig(version)


class ThangsConfig(object):
    def __init__(self, version=None):
        self.config_obj = configparser.ConfigParser()
        self.config_path = os.path.join(
            os.path.dirname(__file__), 'prod_config.ini')
        self.config_obj.read(self.config_path)
        self.thangs_config = self.config_obj['thangs']
        self.version = str(version)
    pass
