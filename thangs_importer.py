import bpy
import os
import urllib
import requests
import shutil
import webbrowser
import queue
import time

from config import get_config
from api_clients import get_thangs_events
from .model_importer import import_model
from services import ThangsLoginService, get_threading_service
from login_token_cache import get_api_token


_thangs_api = None


def get_thangs_api():
    global _thangs_api
    return _thangs_api


def initialize_thangs_api(callback):
    global _thangs_api
    _thangs_api = ThangsApi(callback)


class Config:
    THANGS_MODEL_DIR = bpy.app.tempdir


class Utils:
    def clean_downloaded_model_dir(modelTitle):
        shutil.rmtree(os.path.join(Config.THANGS_MODEL_DIR, modelTitle))

    def clean_node_hierarchy(objects, root_name):
        """
        Removes the useless nodes in a hierarchy
        TODO: Keep the transform (might impact Yup/Zup)
        """
        # Find the parent object
        root = None
        for object in objects:
            if object.parent is None:
                root = object
        if root is None:
            return None

        # Go down its hierarchy until one child has multiple children, or a single mesh
        # Keep the name while deleting objects in the hierarchy
        diverges = False
        while diverges == False:
            children = root.children
            if children is not None:

                if len(children) > 1:
                    diverges = True
                    root.name = root_name

                if len(children) == 1:
                    if children[0].type != "EMPTY":
                        diverges = True
                        root.name = root_name
                        if children[0].type == "MESH":  # should always be the case
                            matrixcopy = children[0].matrix_world.copy()
                            children[0].parent = None
                            children[0].matrix_world = matrixcopy
                            bpy.data.objects.remove(root)
                            children[0].name = root_name
                            root = children[0]

                    elif children[0].type == "EMPTY":
                        diverges = False
                        matrixcopy = children[0].matrix_world.copy()
                        children[0].parent = None
                        children[0].matrix_world = matrixcopy
                        bpy.data.objects.remove(root)
                        root = children[0]
            else:
                break

        # Select the root Empty node
        root.select_set(True)


class ThangsApi:
    def __init__(self, callback=None):
        self.import_callback = callback
        self.Thangs_Config = get_config()
        self.amplitude = get_thangs_events()

        self.login_service = ThangsLoginService()

        self.execution_queue = queue.Queue()

        self.headers = {}

        self.failed = False
        self.importing = False
        self.import_limit = False

        self.deviceId = ""
        self.LicenseURL = ""

        self.model = None
        self.downloaded_files_list = []
        self.download_start_time = None
        self.download_end_time = None
        pass

    class DownloadedFile():
        def __init__(self, partId, partFileName, downloadedFileName):
            self.partId = partId
            self.partFileName = partFileName
            self.downloadedFileName = downloadedFileName
            pass

    def run_in_main_thread(self, function):
        self.execution_queue.put(function)

    def handle_download(self, part, LicenseURL):
        self.model = part
        self.LicenseURL = LicenseURL
        self.download_file()
        return True

    def download_file(self):
        self.importing = True
        self.failed = False

        if self.LicenseURL != "":
            webbrowser.open(self.LicenseURL, new=0, autoraise=True)

        print("Downloading...")
        self.amplitude.send_amplitude_event("Thangs Blender Addon - download model started", event_properties={
            'extension': self.model.fileType,
            'domain': self.model.domain,
        })

        self.model_folder_path = os.path.join(
            Config.THANGS_MODEL_DIR, self.model.partId)
        print("Model Folder:", self.model_folder_path)
        print("Model ID:", self.model.partId)
        print("Model Title:", self.model.partFileName)

        fileExists = False
        for item in self.downloaded_files_list:
            if item.partId == self.model.partId and item.partFileName == self.model.partFileName:
                fileDownloaded = item.downloadedFileName
                fileExists = True
                break

        if not fileExists:
            if not get_api_token():
                self.login_service.login_user(get_threading_service().wrap_up_threads)
            headers = {"Authorization": "Bearer " + get_api_token(), }
            print("URL:", self.Thangs_Config.thangs_config['url'] + "api/models/parts/" + str(
                self.model.partId) + "/download-url")
            try:
                response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(self.model.partId)+"/download-url", headers=headers)
                response.raise_for_status()
            except Exception as e:
                if response.status_code == 429:
                    self.import_limit = True
                    self.importing = False
                    self.amplitude.send_amplitude_event("Thangs Blender Addon - download model failed",
                                                        event_properties={
                                                            'extension': self.model.fileType,
                                                            'domain': self.model.domain,
                                                            'exception': str(e),
                                                        })
                    return
                elif response.status_code == 401 or response.status_code == 403:
                    try:
                        self.login_service.login_user(get_threading_service().wrap_up_threads)
                        headers = {"Authorization": "Bearer " + get_api_token(), }
                        response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(self.model.partId)+"/download-url", headers=headers)
                        response.raise_for_status()
                    except Exception as ex:
                        self.importing = False
                        self.amplitude.send_amplitude_event("Thangs Blender Addon - download model failed",
                                                            event_properties={
                                                                'extension': self.model.fileType,
                                                                'domain': self.model.domain,
                                                                'exception': str(ex),
                                                            })
                        return
                else:
                    self.importing = False
                    self.amplitude.send_amplitude_event("Thangs Blender Addon - download model failed",
                                                        event_properties={
                                                            'extension': self.model.fileType,
                                                            'domain': self.model.domain,
                                                            'exception': str(e),
                                                        })
                    return
            self.import_limit = False
            responseData = response.json()
            modelURL = responseData["downloadUrl"]

            if modelURL is None:
                print('Url is None')
                return

            try:
                r = requests.get(modelURL, stream=True)
                r.raise_for_status()
                self.amplitude.send_amplitude_event("Thangs Blender Addon - download model success",
                                                    event_properties={
                                                        'extension': self.model.fileType,
                                                        'domain': self.model.domain,
                                                    })
            except requests.HTTPError as e:
                self.amplitude.send_amplitude_event("Thangs Blender Addon - download model failed",
                                                    event_properties={
                                                        'extension': self.model.fileType,
                                                        'domain': self.model.domain,
                                                        'exception': str(e),
                                                    })
                self.importing = False
                return

            urlDecoded = urllib.parse.unquote(modelURL)

            split_tup_top = os.path.splitext(urlDecoded)
            file_extension = split_tup_top[1]
            file_extension = file_extension.replace('"', '')
            self.file_extension = file_extension.lower()

            fileindex = urlDecoded.rfind('/', urlDecoded.rfind('filename="'))
            if fileindex == -1:
                fileindex = urlDecoded.rfind('filename="')
                filename = urlDecoded[-(len(urlDecoded) - (fileindex + 10)):]
            else:
                filename = urlDecoded[-(len(urlDecoded) - (fileindex + 1)):]

            filename = filename.replace('"', '')
            self.file_path = os.path.join(self.model_folder_path, filename)

            print("Starting Download")
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            os.makedirs(self.model_folder_path)
            with open(self.file_path, "wb") as f:
                total_length = r.headers.get('content-length')
                if total_length is None:  # no content length header
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=1024*100):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        wm.progress_update(done)
                        print("Filedata:", done)

            self.downloaded_files_list.append(self.DownloadedFile(
                partId=self.model.partId, partFileName=self.model.partFileName, downloadedFileName=filename))
            wm.progress_end()
        else:
            self.file_path = os.path.join(
                self.model_folder_path, fileDownloaded)

            split_tup_top = os.path.splitext(fileDownloaded)
            self.file_extension = split_tup_top[1]
            print('Model Already Downloaded')

        self.run_in_main_thread(self.import_callback)

    def calc_duration(self, start_time, end_time):
        if start_time == None or end_time == None: return 'error'
        else: return end_time - start_time

    def import_model(self):
        try:
            if self.file_extension == '.zip':
                self.zipped_file_path = self.file_path
                if self.unzip_archive():
                    split_tup_top = os.path.splitext(self.model.partFileName)
                    self.file_extension = split_tup_top[1]
                    self.file_path = os.path.join(self.temp_dir, self.model.partFileName)
                else:
                    raise Exception("Unzipping didn't complete")
        except Exception as e:
            print('Unzip error')
            self.amplitude.send_amplitude_event("Thangs Blender Addon - import model", event_properties={
                'extension': self.model.fileType,
                'domain': self.model.domain,
                'success': False,
                'exception': str(e),
            })
            self.failed = True
            self.importing = False
            return
        
        print("File Path:", self.file_path)
        print("File Extension:", self.file_extension)

        import_result = None
        try:
            import_result = import_model(
                self.file_extension, self.file_path)
            print(import_result)
            self.failed = import_result.failed
            self.importing = import_result.importing
        except Exception as e:
            print('Failed to Import')
            download_model_duration_seconds = self.calc_duration(self.download_start_time, self.download_end_time)
            import_model_duration_seconds = self.calc_duration(self.download_end_time, time.time()) 
            self.failed = import_result.failed
            self.importing = import_result.importing
            self.amplitude.send_amplitude_event("Thangs Blender Addon - import model", event_properties={
                'extension': self.model.fileType,
                'domain': self.model.domain,
                'success': False,
                'download_model_duration_seconds': download_model_duration_seconds,
                'import_model_duration_seconds': import_model_duration_seconds,
                'exception': str(e),
            })
        download_model_duration_seconds = self.calc_duration(self.download_start_time, self.download_end_time)
        import_model_duration_seconds = self.calc_duration(self.download_end_time, time.time())
        self.amplitude.send_amplitude_event("Thangs Blender Addon - import model", event_properties={
                'extension': self.model.fileType,
                'domain': self.model.domain,
                'success': True,
                'download_model_duration_seconds': download_model_duration_seconds,
                'import_model_duration_seconds': import_model_duration_seconds
            })
        
        return

    def unzip_archive(self):
        if os.path.exists(self.zipped_file_path):
            import zipfile
            try:
                zip_ref = zipfile.ZipFile(self.zipped_file_path, 'r')
                extract_dir = os.path.dirname(self.zipped_file_path)
                zip_ref.extractall(extract_dir)
                zip_ref.close()
            except zipfile.BadZipFile:
                print('Error when unzipping file')
                os.remove(self.zipped_file_path)
                return False

            files = os.listdir(extract_dir)
            files = [f for f in files if os.path.isfile(extract_dir + '/' + f)]
            print(*files, sep="\n")

            for file in files:
                self.downloaded_files_list.append(self.DownloadedFile(
                    partId=self.model.partId, partFileName=self.model.partFileName, downloadedFileName=file))
            return True
        else:
            print('Archive doesn\'t exist')
            return False
