import bpy
import urllib
import threading

from config import get_config
from api_clients import thangs_login_client
from time import sleep
from typing import Optional

from .thangs_login_service import ThangsLoginService
from api_clients import ThangsFileSyncClient


class ThangsSyncService:
    __model_id = None

    def __init__(self):
        self.__login_service = ThangsLoginService()

    def sync_current_blender_file(self):
        # TODO this needs to not be so hacky
        token = self.__login_service.get_api_token()
        filename = bpy.path.basename(bpy.context.blend_data.filepath)
        sync_client = ThangsFileSyncClient()

        # TODO gonna need an if block to handle model id later
        upload_urls = sync_client.get_upload_urls(token, [filename], ThangsSyncService.__model_id)

        encoded_upload_url = upload_urls[0]['signedUrl']
        query_string_index = encoded_upload_url.index('?X-Goog-Algorithm')
        upload_url_base = encoded_upload_url[:query_string_index]
        upload_url_query_string = urllib.parse.unquote(encoded_upload_url[query_string_index:])
        upload_url = upload_url_base + upload_url_query_string

        sync_client.upload_current_blend_file(token, upload_url)
        if ThangsSyncService.__model_id:
            sync_client.update_model_from_current_blend_file(token, upload_urls[0]['newFileName'], ThangsSyncService.__model_id)
        else:
            model_ids = sync_client.create_model_from_current_blend_file(token, filename, upload_urls[0]['newFileName'])
            model_id = model_ids[0]
            # TODO should be saving this to a datablock
            ThangsSyncService.__model_id = model_id
