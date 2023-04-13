import requests
import uuid
from typing import TypedDict, Optional

from config import get_config


class AccessGrantUser(TypedDict):
    id: int
    username: str
    email: str


class AccessGrant(TypedDict):
    expires: str
    TOKEN: str
    user: AccessGrantUser


class ThangsLoginClient:
    def __init__(self):
        self.thangs_config = get_config()

    def get_browser_authenticate_url(self, challenge_id: uuid.UUID) -> str:
        return f"{self.thangs_config.thangs_config['url']}profile/client-access-grant?verifierCode={challenge_id}&version=blender-addon&appName=Thangs+Blender+addon"

    def check_access_grant(self, challenge_id: uuid.UUID, attempt: int) -> Optional[AccessGrant]:
        check_grant_url = f"{self.thangs_config.thangs_config['url']}api/users/access-grant/{challenge_id}/check?attempts={attempt}"
        response = requests.get(check_grant_url)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
