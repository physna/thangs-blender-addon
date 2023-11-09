import logging
import os
import json
from typing import Optional
from config import get_config


log = logging.getLogger(__name__)
_login_token_cache = None

def initialize_token(main_addon_file_location: str):
    global _login_token_cache
    _login_token_cache = LoginTokenCache(main_addon_file_location)

def set_token(token):
    global _login_token_cache
    _login_token_cache.cached_token = token

def get_bearer_json_file_location(main_addon_file_location = None) -> str:
    global _login_token_cache
    if main_addon_file_location == None:
        file_location = get_config().main_addon_file_location
    else:
        file_location = main_addon_file_location
    bearer_location = os.path.join(os.path.dirname(file_location), 'bearer.json')
    return bearer_location

def get_api_token() -> Optional[str]:
    global _login_token_cache
    if _login_token_cache.cached_token:
        return _login_token_cache.cached_token

    bearer_location = get_bearer_json_file_location()
    if not os.path.exists(bearer_location):
        set_token(None)
        return _login_token_cache.cached_token
    bearer_file = open(bearer_location)
    data = json.load(bearer_file)
    set_token(data["bearer"])
    return _login_token_cache.cached_token

def initialize_api_token(main_addon_file_location = None):
    global _login_token_cache

    bearer_location = get_bearer_json_file_location(main_addon_file_location)
    if not os.path.exists(bearer_location):
        return None
    bearer_file = open(bearer_location)
    data = json.load(bearer_file)
    return data["bearer"]

class LoginTokenCache(object):
    def __init__(self, main_addon_file_location: str):
        self.cached_token = initialize_api_token(main_addon_file_location)
    pass
