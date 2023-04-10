import logging
import configparser
import os

log = logging.getLogger(__name__)
_thangs_config = None


def get_config():
    global _thangs_config
    return _thangs_config


def initialize(version, main_addon_file_location: str):
    global _thangs_config
    _thangs_config = ThangsConfig(version, main_addon_file_location)


class ThangsConfig(object):
    def __init__(self, version, main_addon_file_location: str):
        """ Don't call this to get the config.  Use get_config(). """
        self.config_obj = configparser.ConfigParser()
        self.main_addon_file_location: str = main_addon_file_location
        self.config_path = os.path.join(
            os.path.dirname(main_addon_file_location), 'config.ini')
        self.config_obj.read(self.config_path)
        self.thangs_config = self.config_obj['thangs']
        self.version = str(version)
    pass
