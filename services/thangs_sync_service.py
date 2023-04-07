import json
import bpy
import urllib
import ntpath
import datetime
import threading
import concurrent.futures

from bpy.app.handlers import persistent
from typing import List, TypedDict
from .thangs_login_service import ThangsLoginService
from api_clients import ThangsFileSyncClient, UploadUrlResponse, ThangsModelsClient
# TODO I hate putting this in here, need to figure out how to separate the UI updates from the sync process
from UI.common import redraw_areas


class SyncInfo(TypedDict):
    model_id: int
    last_sync_time: datetime.datetime
    thumbnail_url: str
    version_sha: str
    sync_on_save: bool
    is_public: bool


class ThangsSyncService:
    __SYNC_DATA_BLOCK_NAME__ = 'thangs_blender_addon_sync_data'

    def __init__(self):
        self.__login_service = ThangsLoginService()
        self.__sync_thread: threading.Thread = None
        self.__sync_thread_stop_event = threading.Event()

    def start_sync_process(self):
        if self.__sync_thread:
            self.cancel_running_sync_process()
        self.__sync_thread = threading.Thread(target=self.__sync_current_blender_file).start()
        return

    def cancel_running_sync_process(self):
        if self.__sync_thread:
            self.__sync_thread_stop_event.set()
            self.__sync_thread.join()
            self.__reset_sync_process()

    def __reset_sync_process(self):
        self.__sync_thread = None
        self.__sync_thread_stop_event.clear()
        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = ''
        redraw_areas()

    def __sync_current_blender_file(self):
        if self.__sync_thread_stop_event.is_set():
            return

        # TODO this shouldn't live here but it's good enough for a test
        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 1 of 6)'
        redraw_areas()

        # TODO need to handle 401s, 403s
        token = self.__login_service.get_api_token()
        filename = bpy.path.basename(bpy.context.blend_data.filepath)
        sync_client = ThangsFileSyncClient()

        model_id = None
        is_saved_as_public_model: bool = None
        sync_data = self.get_sync_info_text_block()
        if sync_data:
            model_id = sync_data['model_id']
            is_saved_as_public_model = sync_data['is_public']

        upload_urls = sync_client.get_upload_url_for_blend_file(token, [filename], model_id)

        if self.__sync_thread_stop_event.is_set():
            return

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 2 of 6)'
        redraw_areas()

        encoded_upload_url = upload_urls[0]['signedUrl']
        query_string_index = encoded_upload_url.index('?X-Goog-Algorithm')
        upload_url_base = encoded_upload_url[:query_string_index]
        upload_url_query_string = urllib.parse.unquote(encoded_upload_url[query_string_index:])
        upload_url = upload_url_base + upload_url_query_string

        sync_client.upload_file_to_storage(upload_url, bpy.context.blend_data.filepath)

        if self.__sync_thread_stop_event.is_set():
            return

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 3 of 6)'
        redraw_areas()

        # TODO need to do something to not reupload duplicate files
        image_upload_urls: List[UploadUrlResponse] = []
        details_need_updated = False
        if len(bpy.data.images):
            image_file_paths = set([i.filepath for i in bpy.data.images if i.filepath])
            if image_file_paths:
                image_upload_urls = sync_client.get_upload_url_for_attachment_files(token, [ntpath.basename(i) for i in
                                                                                            image_file_paths], model_id)

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    upload_futures: List[concurrent.futures.Future] = []
                    for image_path in image_file_paths:
                        if self.__sync_thread_stop_event.is_set():
                            return

                        image_filename = ntpath.basename(image_path)
                        upload_url_response = next((iuu for iuu in image_upload_urls if iuu['fileName'] == image_filename))
                        future = executor.submit(sync_client.upload_file_to_storage, upload_url_response['signedUrl'], bpy.path.abspath(image_path))
                        upload_futures.append(future)

                        details_need_updated = True

                    for future in upload_futures:
                        future.result()

        if bpy.context.scene.thangs_blender_addon_sync_panel_sync_as_public_model != is_saved_as_public_model:
            details_need_updated = True

        if self.__sync_thread_stop_event.is_set():
            return

        models_client = ThangsModelsClient()
        if model_id and details_need_updated:
            pre_sync_model_data = models_client.get_model(token, model_id)
            sync_client.update_thangs_model_details(token, model_id,
                                                    [r['newFileName'] for r in image_upload_urls],
                                                    bpy.context.scene.thangs_blender_addon_sync_panel_sync_as_public_model,
                                                    pre_sync_model_data['name'],
                                                    pre_sync_model_data['description'],
                                                    pre_sync_model_data['material'],
                                                    pre_sync_model_data['weight'],
                                                    pre_sync_model_data['height'],
                                                    pre_sync_model_data['category'],
                                                    pre_sync_model_data['license'],
                                                    pre_sync_model_data['folderId']
                                                    )

        if self.__sync_thread_stop_event.is_set():
            return

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 4 of 6)'
        redraw_areas()

        sha = '0000'
        if model_id:
            version_response = sync_client.update_model_from_current_blend_file(token, upload_urls[0]['newFileName'],
                                                                                model_id)
            sha = version_response['sha']
        else:
            model_ids = sync_client.create_model_from_current_blend_file(token, filename, upload_urls[0]['newFileName'],
                                                                         [r['newFileName'] for r in image_upload_urls],
                                                                         bpy.context.scene.thangs_blender_addon_sync_panel_sync_as_public_model)
            model_id = model_ids[0]

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 5 of 6)'
        redraw_areas()

        model_data = models_client.get_model(token, model_id)

        bpy.context.scene.thangs_blender_addon_sync_panel_status_message = 'Syncing model (Step 6 of 6)'
        redraw_areas()

        last_sync_time = datetime.datetime.utcnow()
        sync_data_to_save = SyncInfo()
        sync_data_to_save['model_id'] = model_id
        sync_data_to_save['last_sync_time'] = last_sync_time
        sync_data_to_save['version_sha'] = sha
        sync_data_to_save['sync_on_save'] = bpy.context.scene.thangs_blender_addon_sync_panel_sync_on_save
        sync_data_to_save['is_public'] = bpy.context.scene.thangs_blender_addon_sync_panel_sync_as_public_model
        sync_data_to_save['thumbnail_url'] = model_data['parts'][0]['thumbnailUrl']
        self.save_sync_info_text_block(sync_data_to_save)

        self.__reset_sync_process()

    def save_sync_info_text_block(self, sync_info: SyncInfo):
        sync_data_block = None
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
        else:
            sync_data_block = bpy.data.texts.new(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__)

        sync_info['last_sync_time'] = sync_info['last_sync_time'].isoformat()

        sync_data_block.from_string(json.dumps(sync_info))

        supress_sync_on_save()
        bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
        enable_sync_on_save()

    def remove_sync_info_text_block(self):
        bpy.data.texts.remove(bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__])

    def get_sync_info_text_block(self) -> SyncInfo:
        if bpy.data.texts.find(ThangsSyncService.__SYNC_DATA_BLOCK_NAME__) != -1:
            sync_data_block = bpy.data.texts[ThangsSyncService.__SYNC_DATA_BLOCK_NAME__]
            sync_data = json.loads(sync_data_block.as_string())
            parsed_data = SyncInfo()
            parsed_data['model_id'] = sync_data['model_id']
            parsed_data['thumbnail_url'] = sync_data['thumbnail_url']
            parsed_data['version_sha'] = sync_data['version_sha']
            parsed_data['sync_on_save'] = sync_data['sync_on_save']
            parsed_data['is_public'] = sync_data['is_public']
            parsed_data['last_sync_time'] = self.convert_utc_timestamp_to_local(
                datetime.datetime.fromisoformat(sync_data['last_sync_time']))
            return parsed_data

        return None

    def convert_utc_timestamp_to_local(self, timestamp):
        return timestamp.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


__sync_service__: ThangsSyncService = None


def get_sync_service():
    global __sync_service__

    if not __sync_service__:
        __sync_service__ = ThangsSyncService()

    return __sync_service__


__supress_sync_on_save_handler__: bool = True


@persistent
def sync_on_save_handler(dummy):
    global __supress_sync_on_save_handler__

    if __supress_sync_on_save_handler__:
        return

    if not bpy.context.scene.thangs_blender_addon_sync_panel_sync_on_save:
        return

    print('syncing from save handler')
    sync_service = get_sync_service()
    sync_service.start_sync_process()


def supress_sync_on_save():
    global __supress_sync_on_save_handler__

    __supress_sync_on_save_handler__ = True


def enable_sync_on_save():
    global __supress_sync_on_save_handler__

    __supress_sync_on_save_handler__ = False
