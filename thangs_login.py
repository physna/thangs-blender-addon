from time import sleep 
from .config import get_config, ThangsConfig
import uuid, webbrowser, requests, threading

GRANT_CHECK_INTERVAL_SECONDS=0.5 # 500 milliseconds
MAX_ATTEMPTS=600 # 5 minutes worth
BLENDER_IS_CLOSED = False

def stop_access_grant():
    global BLENDER_IS_CLOSED
    BLENDER_IS_CLOSED = True

class ThangsLogin(threading.Thread):
    token = {}

    def __init__(self):
        super().__init__()

        self.config = ThangsConfig().thangs_config

    def startLoginFromBrowser(self):
        return self.start()

    def run(self,*args,**kwargs):
        global BLENDER_IS_CLOSED
        global MAX_ATTEMPTS
        codeChallengeId = self.authenticate()

        done = False
        attempts = 0

        while done == False and BLENDER_IS_CLOSED == False and attempts < MAX_ATTEMPTS:
            response = self.checkAccessGrant(codeChallengeId, attempts)

            if response.status_code == 200:
                done = True
                token = response
                self.token = token.json()
            elif response.status_code == 401:
                done = True
            else:
                attempts = attempts + 1

    def apiAccessGrantUrl(self, codeChallengeId, attempts):
        return f"{self.config['apiUrl']}users/access-grant/{codeChallengeId}/check?attempts={attempts}"

    def authenticate(self):
        codeChallengeId = uuid.uuid4()

        webbrowser.open(f"{self.config['url']}/profile/client-access-grant?verifierCode={codeChallengeId}&version=blender-addon&appName=blender+addon")

        return codeChallengeId

    def checkAccessGrant(self, codeChallengeId, attempts=0):
        global GRANT_CHECK_INTERVAL_SECONDS
        sleep(GRANT_CHECK_INTERVAL_SECONDS)
        apiUrl = self.apiAccessGrantUrl(codeChallengeId, attempts)
        return requests.get(apiUrl)
