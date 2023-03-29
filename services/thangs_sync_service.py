import json
import bpy
import urllib

from .thangs_login_service import ThangsLoginService
from api_clients import ThangsFileSyncClient

class ThangsSyncService:
    __SYNC_DATA_BLOCK_NAME__ = 'thangs_blender_addon_sync_data'

    def __init__(self):
        self.__login_service = ThangsLoginService()

    def sync_current_blender_file(self):
        # TODO this needs to not be so hacky
        token = self.__login_service.get_api_token()
        filename = bpy.path.basename(bpy.context.blend_data.filepath)
        sync_client = ThangsFileSyncClient()

        model_id = None
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
            sync_data = json.loads(sync_data_block.as_string())
            model_id = sync_data['model_id']

        upload_urls = sync_client.get_upload_urls(token, [filename], model_id)

        encoded_upload_url = upload_urls[0]['signedUrl']
        query_string_index = encoded_upload_url.index('?X-Goog-Algorithm')
        upload_url_base = encoded_upload_url[:query_string_index]
        upload_url_query_string = urllib.parse.unquote(encoded_upload_url[query_string_index:])
        upload_url = upload_url_base + upload_url_query_string

        sync_client.upload_current_blend_file(token, upload_url)
        if model_id:
            sync_client.update_model_from_current_blend_file(token, upload_urls[0]['newFileName'], model_id)
        else:
            model_ids = sync_client.create_model_from_current_blend_file(token, filename, upload_urls[0]['newFileName'])
            model_id = model_ids[0]

        sync_data_block = None
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
        else:
            sync_data_block = bpy.data.texts.new(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__)

        sync_data = {
            'model_id': model_id
        }

        sync_data_block.from_string(json.dumps(sync_data))
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)