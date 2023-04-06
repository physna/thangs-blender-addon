import requests
from typing import List, TypedDict
from config import get_config


# These are incomplete because we don't need the rest of it right now
class PartsResponse(TypedDict):
    thumbnailUrl: str
    name: str
    description: str
    material: str
    weight: str
    height: str
    category: str
    license: str
    folderId: str


class GetModelResponse(TypedDict):
    id: str
    name: str
    isPublic: bool
    parts: List[PartsResponse]


class ThangsModelsClient:
    def __init__(self):
        self.thangs_config = get_config()

    def get_model(self, api_token: str, model_id: int) -> GetModelResponse:
        url = f'{self.thangs_config.thangs_config["url"]}api/models/{model_id}'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        return response_data

