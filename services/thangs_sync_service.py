import bpy
import threading

from config import get_config
from api_clients import thangs_login_client
from time import sleep
from typing import Optional

from .thangs_login_service import ThangsLoginService
from api_clients import ThangsFileSyncClient


class ThangsSyncService:
    def __init__(self):
        self.__login_service = ThangsLoginService()

    def sync_current_blender_file(self):
        # TODO this needs to not be so hacky
        token = self.__login_service.get_api_token()
        filename = bpy.path.basename(bpy.context.blend_data.filepath)
        sync_client = ThangsFileSyncClient()
        upload_urls = sync_client.get_upload_urls(token, [filename])

        sync_client.upload_current_blend_file(token, upload_urls[0]['signedUrl'])
        sync_client.create_model_from_current_blend_file(token, filename, upload_urls[0]['newFileName'])
