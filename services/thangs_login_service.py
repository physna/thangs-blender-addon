import threading
import uuid
import json
import webbrowser
import requests

from api_clients import thangs_login_client
from time import sleep
from login_token_cache import set_token, get_bearer_json_file_location, get_api_token

class ThangsLoginService:
    __GRANT_CHECK_INTERVAL_SECONDS = 0.5  # 500 milliseconds
    __MAX_ATTEMPTS = 600  # 5 minutes worth

    def __init__(self):
        self.__login_client = thangs_login_client.ThangsLoginClient()

    def login_user(self, cancellation_event: threading.Event = None) -> None:
        if get_api_token:
            set_token(None)

        challenge_id = uuid.uuid4()
        webbrowser.open(self.__login_client.get_browser_authenticate_url(challenge_id))

        attempts = 0

        while attempts < ThangsLoginService.__MAX_ATTEMPTS and not (cancellation_event and cancellation_event.is_set()):
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
                with open(get_bearer_json_file_location(), 'w') as json_file:
                    json.dump(bearer, json_file)
                set_token(response['TOKEN'])

                return
            except requests.HTTPError as e:
                if e.response.status_code == 401:
                    print("Unsuccessful Login, 401 returned")
                    return
                raise

        print("Unsuccessful Login, max attempts exceeded")
