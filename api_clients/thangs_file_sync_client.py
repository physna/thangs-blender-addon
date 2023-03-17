import os

import requests
import bpy
import os
from typing import List

from .. import ThangsConfig


class ThangsFileSyncClient:
    def __init__(self):
        self.Thangs_Config = ThangsConfig()

    def get_upload_urls(self, api_token: str, file_names: List[str]):
        url = f'{self.Thangs_Config.thangs_config["url"]}api/models/upload-urls'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }
        json = {
            'fileNames': file_names
        }
        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        print(response_data)
        return response_data

    # TODO probably should be passing things in rather than assuming the current blend file, but for POC this is fine
    def upload_current_blend_file(self, api_token: str, url: str) -> None:
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/octet-stream'
        }
        file = {'content': open(bpy.context.blend_data.filepath, 'rb')}
        response = requests.put(url, headers=headers, files=file)
        response.raise_for_status()
        return

    # TODO probably should be passing things in rather than assuming the current blend file, but for POC this is fine
    def create_model_from_current_blend_file(self, api_token: str, filename: str, new_file_name: str):
        url = f'{self.Thangs_Config.thangs_config["url"]}api/models'
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
