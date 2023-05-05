import requests
import bpy
import os
import pathlib
import asyncio
from typing import List, TypedDict
from config import get_config
from .thangs_events import get_thangs_events


class UploadUrlResponse(TypedDict):
    fileName: str
    signedUrl: str
    newFileName: str


class VersionModelResponse(TypedDict):
    sha: str


class ThangsFileSyncClient:
    def __init__(self):
        self.__thangs_config = get_config()
        self.__events_client = get_thangs_events()

    def get_upload_url_for_blend_file(self, api_token: str, file_names: List[str], model_id: int = None) -> List[UploadUrlResponse]:
        url = f'{self.__thangs_config.thangs_config["url"]}api/models/upload-urls'
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
        url = f'{self.__thangs_config.thangs_config["url"]}api/attachments/upload-urls'
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
            try:
                response = requests.put(url, headers=headers, data=file)
                response.raise_for_status()
            except Exception as e:
                try:
                    response = requests.put(url, headers=headers, data=file)
                    response.raise_for_status()
                except Exception as e2:
                    get_thangs_events().send_amplitude_event("Thangs Blender Addon - failed uploading file to storage", event_properties={
                        'extension': pathlib.Path(file_path).suffix,
                        'exceptions': [str(e), str(e2)],
                    })
                    raise Exception('Failed to upload a file to storage')

    def update_thangs_model_details(self, api_token: str, model_id: int, reference_files: List[str], is_public: bool,
                                    name: str, description: str, material: str, weight: str, height: str, category: str,
                                    model_license: str, folder_id: str) -> None:
        url = f'{self.__thangs_config.thangs_config["url"]}api/models/{model_id}/details'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        coalesced_folder_id = folder_id
        if folder_id is None:
            coalesced_folder_id = ''

        json = {
            'name': name,
            'isPublic': is_public,
            'description': description,
            'material': material,
            'weight': weight,
            'height': height,
            'category': category,
            'license': model_license,
            'folderId': coalesced_folder_id,
            'attachments': [],
            'referenceFiles': [{'filename': r} for r in reference_files],
        }
        response = requests.put(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        return response_data

    def create_asset_group(self, api_token: str, new_file_name: str,
                           reference_files: List[str]) -> List[int]:
        url = f'{self.__thangs_config.thangs_config["url"]}api/v2/models/assetGroup'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        reference_files_no_prefix = []

        for item in reference_files:
            if item.startswith('uploads/attachments/'):
                reference_files_no_prefix.append(
                    item[len('uploads/attachments/'):])
            else:
                reference_files_no_prefix.append(item)

        json = {
            'assets': [{
                'modelFiles': [new_file_name],
                'supportingFiles': reference_files_no_prefix
            }]
        }

        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        response_data = response.json()
        return response_data

    def poll_asset_group(self, api_token: str, asset_group_id: int):

        async def retry(retry_attempt: int, time_to_retry: int):
            if retry_attempt > 10:
                time_to_retry = 5
            print('Polling asset group. Attempt number', i,
                  ' Waiting', time_to_retry, 'seconds to retry.')
            await asyncio.sleep(time_to_retry)

        retry_attempt = 130
        time_to_retry = 2
        for i in range(1, retry_attempt):
            response = self.get_asset_group_status(api_token, asset_group_id)

            if response.status_code != 200:
                asyncio.run(retry(i, time_to_retry))
            else:
                response_data = response.json()
                if response_data['isComplete'] == True:
                    print('Asset group complete.')
                    break
                elif response_data['isComplete'] == False:
                    asyncio.run(retry(i, time_to_retry))

    def get_asset_group_status(self, api_token: str, asset_group_id: int):
        url = f'{self.__thangs_config.thangs_config["url"]}api/v2/models/assetGroup/{asset_group_id}'
        headers = {
            'Authorization': f'Bearer {api_token}',
        }

        response = requests.get(url, headers=headers)

        return response

    def create_model_from_current_blend_file_with_asset_group(self, api_token: str, filename: str, new_file_name: str,
                                                              reference_files: List[str], is_public: bool, asset_group_id: int) -> List[int]:
        url = f'{self.__thangs_config.thangs_config["url"]}api/v2/models/assetGroup/{asset_group_id}/model'
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
        return response_data

    def create_model_from_current_blend_file(self, api_token: str, filename: str, new_file_name: str,
                                             reference_files: List[str], is_public: bool) -> List[int]:
        url = f'{self.__thangs_config.thangs_config["url"]}api/models'
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
        return response_data

    def update_model_from_current_blend_file(self, api_token: str, new_file_name: str,
                                             model_id: int) -> VersionModelResponse:
        url = f'{self.__thangs_config.thangs_config["url"]}api/v2/models/{model_id}'
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
        return response_data
