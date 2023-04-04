import json
import bpy
import urllib
import ntpath
import datetime

from typing import List, TypedDict
from .thangs_login_service import ThangsLoginService
from api_clients import ThangsFileSyncClient, UploadUrlResponse
# TODO I hate putting this in here, need to figure out how to separate the UI updates from the sync process
from UI.common import redraw_areas


class SyncInfo(TypedDict):
    model_id: int
    last_sync_time: datetime.datetime


class ThangsSyncService:
    __SYNC_DATA_BLOCK_NAME__ = 'thangs_blender_addon_sync_data'

    def __init__(self):
        self.__login_service = ThangsLoginService()

    def sync_current_blender_file(self):
        # TODO this shouldn't live here but it's good enough for a test
        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 1 of 5)'
        redraw_areas()

        # TODO this needs to not be so hacky
        # TODO need to handle 401s, 403s
        token = self.__login_service.get_api_token()
        filename = bpy.path.basename(bpy.context.blend_data.filepath)
        sync_client = ThangsFileSyncClient()

        model_id = None
        sync_data = self.get_sync_info_text_block()
        if sync_data:
            model_id = sync_data['model_id']

        # TODO Upload the blend file
        upload_urls = sync_client.get_upload_url_for_blend_file(token, [filename], model_id)

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 2 of 5)'
        redraw_areas()

        encoded_upload_url = upload_urls[0]['signedUrl']
        query_string_index = encoded_upload_url.index('?X-Goog-Algorithm')
        upload_url_base = encoded_upload_url[:query_string_index]
        upload_url_query_string = urllib.parse.unquote(encoded_upload_url[query_string_index:])
        upload_url = upload_url_base + upload_url_query_string

        # TODO implement retries
        sync_client.upload_file_to_storage(upload_url, bpy.context.blend_data.filepath)

        # TODO Upload reference files, need to do something to not reupload duplicate files

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 3 of 5)'
        redraw_areas()

        image_upload_urls: List[UploadUrlResponse] = []

        if len(bpy.data.images):
            image_file_paths = set([i.filepath for i in bpy.data.images if i.filepath])
            if image_file_paths:
                image_upload_urls = sync_client.get_upload_url_for_attachment_files(token, [ntpath.basename(i) for i in image_file_paths], model_id)
                # TODO should probably run these async with other upload calls so we can do them in parallel
                for image_path in image_file_paths:
                    image_filename = ntpath.basename(image_path)
                    upload_url_response = next((iuu for iuu in image_upload_urls if iuu['fileName'] == image_filename))
                    sync_client.upload_file_to_storage(upload_url_response['signedUrl'], bpy.path.abspath(image_path))

                if model_id:
                    sync_client.update_thangs_model_details(token, model_id, [r['newFileName'] for r in image_upload_urls])

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 4 of 5)'
        redraw_areas()

        if model_id:
            sync_client.update_model_from_current_blend_file(token, upload_urls[0]['newFileName'], model_id)
        else:
            model_ids = sync_client.create_model_from_current_blend_file(token, filename, upload_urls[0]['newFileName'], [r['newFileName'] for r in image_upload_urls])
            model_id = model_ids[0]

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 5 of 5)'
        redraw_areas()

        last_sync_time = datetime.datetime.utcnow()
        sync_data_to_save = SyncInfo()
        sync_data_to_save['model_id'] = model_id
        sync_data_to_save['last_sync_time'] = last_sync_time
        self.save_sync_info_text_block(sync_data_to_save)

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = ''
        redraw_areas()

    def save_sync_info_text_block(self, sync_info: SyncInfo):
        sync_data_block = None
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
        else:
            sync_data_block = bpy.data.texts.new(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__)

        sync_info['last_sync_time'] = sync_info['last_sync_time'].isoformat()

        sync_data_block.from_string(json.dumps(sync_info))
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)

    def remove_sync_info_text_block(self):
        bpy.data.texts.remove(bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__])

    def get_sync_info_text_block(self) -> SyncInfo:
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
            sync_data = json.loads(sync_data_block.as_string())
            parsed_data = SyncInfo()
            parsed_data['model_id'] = sync_data['model_id']
            parsed_data['last_sync_time'] = self.convert_utc_timestamp_to_local(datetime.datetime.fromisoformat(sync_data['last_sync_time']))
            return parsed_data

        return None

    def convert_utc_timestamp_to_local(self, timestamp):
        return timestamp.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
