import os
import uuid
import json
import webbrowser
import requests
import threading

from config import get_config
from api_clients import thangs_login_client
from time import sleep
from typing import Optional


class ThangsLoginService:
    __GRANT_CHECK_INTERVAL_SECONDS = 0.5  # 500 milliseconds
    __MAX_ATTEMPTS = 600  # 5 minutes worth

    def __init__(self):
        self.__cached_token = None
        self.__login_client = thangs_login_client.ThangsLoginClient()

    def __get_bearer_json_file_location(self) -> str:
        bearer_location = os.path.join(
            os.path.dirname(get_config().main_addon_file_location), 'bearer.json')
        return bearer_location

    def get_api_token(self) -> Optional[str]:
        if self.__cached_token:
            return self.__cached_token

        bearer_location = self.__get_bearer_json_file_location()
        if not os.path.exists(bearer_location):
            return None
        bearer_file = open(bearer_location)
        data = json.load(bearer_file)
        return data["bearer"]

    def login_user(self, cancellation_event: threading.Event) -> None:
        if self.__cached_token:
            self.__cached_token = None

        challenge_id = uuid.uuid4()
        webbrowser.open(self.__login_client.get_browser_authenticate_url(challenge_id))

        attempts = 0

        while attempts < ThangsLoginService.__MAX_ATTEMPTS and not cancellation_event.is_set():
            try:
                sleep(self.__GRANT_CHECK_INTERVAL_SECONDS)
                response = self.__login_client.check_access_grant(challenge_id, attempts)
                if not response:
                    attempts += 1
                    continue

                print("Successful Login")
                bearer_token = response['TOKEN']
                bearer = {
                    'bearer': bearer_token,
                }
                with open(self.__get_bearer_json_file_location(), 'w') as json_file:
                    json.dump(bearer, json_file)
                self.__cached_token = response['TOKEN']

                return
            except requests.HTTPError as e:
                if e.response.status_code == 401:
                    print("Unsuccessful Login, 401 returned")
                    return
                raise

        print("Unsuccessful Login, max attempts exceeded")
