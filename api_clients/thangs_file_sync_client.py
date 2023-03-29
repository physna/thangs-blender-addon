import requests
import bpy
import os
from typing import List

from config import get_config


class ThangsFileSyncClient:
    def __init__(self):
        self.thangs_config = get_config()

    def get_upload_urls(self, api_token: str, file_names: List[str], model_id: int = None):
        url = f'{self.thangs_config.thangs_config["url"]}api/models/upload-urls'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }
        json = {
            'fileNames': file_names
        }

        if model_id:
            json['modelId'] = model_id

        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        return response_data

    # TODO probably should be passing things in rather than assuming the current blend file, but for POC this is fine
    def upload_current_blend_file(self, api_token: str, url: str) -> None:
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        with open(bpy.context.blend_data.filepath, 'rb') as file_contents:
            file = file_contents.read()
            response = requests.put(url, headers=headers, data=file)
            response.raise_for_status()

    # TODO probably should be passing things in rather than assuming the current blend file, but for POC this is fine
    def create_model_from_current_blend_file(self, api_token: str, filename: str, new_file_name: str):
        url = f'{self.thangs_config.thangs_config["url"]}api/models'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        json = [{
            'name': bpy.path.display_name_from_filepath(bpy.context.blend_data.filepath),
            'isPublic': False,
            'description': 'Uploaded by Thangs Blender',
            'folderId': '',
            'attachments': [],
            'referenceFiles': [],
            'parts': [{
                'originalFileName': filename,
                'originalPartName': filename,
                'filename': new_file_name,
                'size': os.stat(bpy.context.blend_data.filepath).st_size,
                'isPrimary': True,
                'name': filename,
                'isPublic': False,
            }]
        }]
        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        print(response_data)
        return response_data
    def update_model_from_current_blend_file(self, api_token: str, new_file_name: str, model_id: int):
        url = f'{self.thangs_config.thangs_config["url"]}api/v2/models/{model_id}'
        print(url)
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        json = {
            'files': [{
                'size': os.stat(bpy.context.blend_data.filepath).st_size,
                'filename': new_file_name,
            }]
        }
        print(json)
        response = requests.put(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        print(response_data)
        return response_data
