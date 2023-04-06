import requests
import bpy
import os
from typing import List, TypedDict
from config import get_config

class UploadUrlResponse(TypedDict):
    fileName: str
    signedUrl: str
    newFileName: str

class VersionModelResponse(TypedDict):
    sha: str

# TODO add typings in this file, especially for return values
class ThangsFileSyncClient:
    def __init__(self):
        self.thangs_config = get_config()

    def get_upload_url_for_blend_file(self, api_token: str, file_names: List[str], model_id: int = None) -> List[UploadUrlResponse]:
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

    def get_upload_url_for_attachment_files(self, api_token: str, file_names: List[str], model_id: int = None) -> List[UploadUrlResponse]:
        url = f'{self.thangs_config.thangs_config["url"]}api/attachments/upload-urls'
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

    def upload_file_to_storage(self, url: str, file_path: str) -> None:
        headers = {
            'Content-Type': 'application/octet-stream'
        }
        with open(file_path, 'rb') as file_contents:
            file = file_contents.read()
            response = requests.put(url, headers=headers, data=file)
            response.raise_for_status()

    def update_thangs_model_details(self, api_token: str, model_id: int, reference_files: List[str], is_public: bool) -> None:
        url = f'{self.thangs_config.thangs_config["url"]}api/models/{model_id}/details'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        # TODO much of this needs to be passed in / grabbed from Thangs.  Good enough for PoC for now.
        json = {
            'name': bpy.path.display_name_from_filepath(bpy.context.blend_data.filepath),
            'isPublic': is_public,
            'description': 'Uploaded by Thangs Blender',
            'material': '',
            'weight': '',
            'height': '',
            'category': '',
            'license': '',
            # TODO fix this
            # 'folderId': None,
            'attachments': [],
            'referenceFiles': [{'filename': r} for r in reference_files],
        }
        response = requests.put(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        return response_data

    # TODO probably should be passing things in rather than assuming the current blend file, but for POC this is fine
    def create_model_from_current_blend_file(self, api_token: str, filename: str, new_file_name: str, reference_files: List[str], is_public: bool) -> List[int]:
        url = f'{self.thangs_config.thangs_config["url"]}api/models'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        json = [{
            'name': bpy.path.display_name_from_filepath(bpy.context.blend_data.filepath),
            'isPublic': is_public,
            'description': 'Uploaded by Thangs Blender',
            'folderId': '',
            'attachments': [],
            'referenceFiles': [{'filename': r} for r in reference_files],
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

    def update_model_from_current_blend_file(self, api_token: str, new_file_name: str, model_id: int) -> VersionModelResponse:
        url = f'{self.thangs_config.thangs_config["url"]}api/v2/models/{model_id}'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        json = {
            'files': [{
                'size': os.stat(bpy.context.blend_data.filepath).st_size,
                'filename': new_file_name,
            }]
        }
        response = requests.put(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        print(response_data)
        return response_data
