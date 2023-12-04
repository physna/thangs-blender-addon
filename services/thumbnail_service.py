import os
import requests
import shutil
import bpy

from typing import Optional
from config import get_config


__MODEL_THUMBNAILS_TEMP_DIR__ = os.path.join(bpy.app.tempdir, "model_thumbnails")
__thumbnail_service = None

class ThumbnailService:
    def __init__(self):
        self.__thumbnail_preview_collection = bpy.utils.previews.new()

    def is_thumbnail_loaded(self, model_id: int, sha: str) -> bool:
        return self.__get_model_thumbnail_key(model_id, sha) in self.__thumbnail_preview_collection.keys()

    def load_thumbnail(self, model_id: int, sha: str, thumbnail_url: str):
        if self.is_thumbnail_loaded(model_id, sha):
            return

        thumbnail_key = self.__get_model_thumbnail_key(model_id, sha)

        thumbnail_path = self.__get_thumbnail_path_if_exists(model_id, sha)
        if not thumbnail_path:
            thumbnail_path = self.__download_thumbnail(thumbnail_url, model_id, sha)

        self.__thumbnail_preview_collection.load(thumbnail_key, thumbnail_path, 'IMAGE')
        return

    def get_thumbnail_icon_id(self, model_id: int, sha) -> int:
        return self.__thumbnail_preview_collection.get(self.__get_model_thumbnail_key(model_id, sha)).icon_id

    def __get_model_thumbnail_key(self, model_id: int, sha) -> str:
        return f'{model_id}_{sha}_thumbnail'

    def __get_model_thumbnail_temp_directory(self, model_id: int, sha: str) -> str:
        return os.path.join(__MODEL_THUMBNAILS_TEMP_DIR__, str(model_id), sha)


    def __ensure_model_thumbnail_directory_exists(self, model_id: int, sha: str) -> str:
        temp_directory = self.__get_model_thumbnail_temp_directory(model_id, sha)
        if not os.path.exists(temp_directory):
            os.makedirs(temp_directory)


    def __get_thumbnail_path_if_exists(self, model_id: int, sha: str) -> Optional[str]:
        temp_directory = self.__get_model_thumbnail_temp_directory(model_id, sha)
        if os.path.exists(temp_directory):
            for file in os.listdir(temp_directory):
                if file.startswith('thumbnail.'):
                    return file

        return None


    def __download_thumbnail(self, thumbnail_url: str, model_id: int, sha: str) -> str:
        try:
            r = requests.get(thumbnail_url, stream=True)
            r.raise_for_status()

            thumbnail_url_parsed = thumbnail_url
            query_string_index = thumbnail_url.find('?')
            if query_string_index != -1:
                thumbnail_url_parsed = thumbnail_url_parsed[:query_string_index]

            extension = thumbnail_url_parsed[thumbnail_url_parsed.rindex('.'):]

            self.__ensure_model_thumbnail_directory_exists(model_id, sha)

            path_to_save_to = os.path.join(self.__get_model_thumbnail_temp_directory(model_id, sha), f'thumbnail{extension}')
            with open(path_to_save_to, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(e)
            self.__ensure_model_thumbnail_directory_exists(model_id, sha)

            path_to_save_to = os.path.join(os.path.dirname(get_config().main_addon_file_location), "icons", "image-error-icon.png")

        return path_to_save_to


def get_thumbnail_service() -> ThumbnailService:
    global __thumbnail_service
    if not __thumbnail_service:
        __thumbnail_service = ThumbnailService()

    return __thumbnail_service


