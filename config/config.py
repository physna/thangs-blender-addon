import logging
import configparser
import os
import json
from typing import Optional

log = logging.getLogger(__name__)
_thangs_config = None


def get_config():
    global _thangs_config
    return _thangs_config


def initialize(version, main_addon_file_location: str):
    global _thangs_config
    _thangs_config = ThangsConfig(version, main_addon_file_location)


def set_token(token):
    global _thangs_config
    _thangs_config.cached_token = token


def get_bearer_json_file_location(main_addon_file_location = None) -> str:
    global _thangs_config
    if main_addon_file_location == None:
        file_location = _thangs_config.main_addon_file_location
    else:
        file_location = main_addon_file_location
    bearer_location = os.path.join(os.path.dirname(file_location), 'bearer.json')
    return bearer_location

def get_api_token() -> Optional[str]:
    global _thangs_config
    if _thangs_config.cached_token:
        return _thangs_config.cached_token

    bearer_location = get_bearer_json_file_location()
    if not os.path.exists(bearer_location):
        set_token(None)
        return _thangs_config.cached_token
    bearer_file = open(bearer_location)
    data = json.load(bearer_file)
    set_token(data["bearer"])
    return _thangs_config.cached_token


def initialize_api_token(main_addon_file_location = None):
    global _thangs_config

    bearer_location = get_bearer_json_file_location(main_addon_file_location)
    if not os.path.exists(bearer_location):
        return None
    bearer_file = open(bearer_location)
    data = json.load(bearer_file)
    return data["bearer"]


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
        self.cached_token = initialize_api_token(main_addon_file_location)
    pass
