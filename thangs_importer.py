import os
import urllib
import requests
import shutil
from .config import get_config
from .thangs_events import ThangsEvents
from .thangs_login import ThangsLogin
import platform
import socket
import webbrowser
import json
import queue
import bpy
from bpy.types import WindowManager
import bpy.utils.previews
from bpy.types import (Panel,
                       PropertyGroup,
                       Operator,
                       )
from bpy.props import (StringProperty,
                       PointerProperty,
                       FloatVectorProperty,
                       )
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from bpy.app.handlers import persistent

_thangs_api = None
_files_list = []

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
        self.amplitude = ThangsEvents()

        self.amplitude.deviceId = socket.gethostname().split(".")[0]
        self.amplitude.deviceOs = platform.system()
        self.amplitude.deviceVer = platform.release()
        self.execution_queue = queue.Queue()
        
        self.headers = {}

        self.failed = False
        self.importing = False
        self.import_limit = False

        self.modelIndex = 0
        
        self.deviceId = ""
        self.LicenseURL = ""
        self.fileType = ""
        self.domain = ""
        self.bearer = ""

        self.modelId = ""
        self.modelTitle = ""

        self.model0 = ""
        self.model1 = ""
        self.model2 = ""
        self.model3 = ""
        self.model4 = ""
        self.model5 = ""
        self.model6 = ""
        self.model7 = ""
        self.modelTitle0 = ""
        self.modelTitle1 = ""
        self.modelTitle2 = ""
        self.modelTitle3 = ""
        self.modelTitle4 = ""
        self.modelTitle5 = ""
        self.modelTitle6 = ""
        self.modelTitle7 = ""

        #self.modelIDTest = ""
        #self.modelTitleTest = ""

        #self.access_token = ''
        #self.api_token = ''
        #self.username = ''
        #self.thumbnails = []
        #self.context = ""
        #self.thangs_ui_mode = ''
        #self.modelIds = []
        #self.modelTitles = []
        #self.filePaths = []
        #self.modelInfo = []
        #self.enumItems = []
        #self.licenses = []
        #self.creators = []
        #self.filetype = []
        #self.totalModels = 0
        #self.Counter = 0
        #self.pcoll = ""
        #self.PageNumber = 1
        #self.Directory = ""
        #self.PageTotal = 0
        #self.preview_collections = {}
        #self.eventCall = ""
        #self.CurrentPage = 1
        #self.searching = False
        #self.import_thread = None
        #self.model_thread = None
        #self.query = ""
        #self.ampURL = ''
        #self.model_path = ""
        #self.uid = ""
        pass

    def run_in_main_thread(self, function):
        self.execution_queue.put(function)

    def refresh_bearer(self):
        thangs_login_import = ThangsLogin()
        bearer_location = os.path.join(os.path.dirname(__file__), 'bearer.json')
        os.remove(bearer_location)
        f = open(bearer_location, "x")

        thangs_login_import.startLoginFromBrowser()
        print("Waiting on Login")
        thangs_login_import.token_available.wait()
        print("Setting Bearer")
        bearer = {
            'bearer': str(thangs_login_import.token["TOKEN"]),
        }
        print("Dumping")
        with open(bearer_location, 'w') as json_file:
            json.dump(bearer, json_file)
        
        f = open(bearer_location)
        data = json.load(f)
        self.bearer = data["bearer"]
        f.close()
        return

    def handle_download(self, modelIndex, LicenseURL, fileType, domain):
        print("self.modelId", self.modelId)
        print("self.modelTitle", self.modelTitle)
        self.modelId = str(self.modelId)
        self.modelTitle = str(self.modelTitle)
        print("self.modelId", self.modelId)
        print("self.modelTitle", self.modelTitle)
        
        self.modelIndex = modelIndex
        self.LicenseURL = LicenseURL
        self.fileType = fileType
        self.domain = domain
        self.download_file()
        return True

    def download_file(self):

        self.importing = True
        self.failed = False

        if self.LicenseURL != "":
            webbrowser.open(self.LicenseURL, new=0, autoraise=True)

        print("Downloading...")
        """
        model_title = str(self.modelTitleTest)
        modelID = str(self.modelIDTest)
        if self.modelIndex == 0:
            modelID = str(self.model0)
            model_title = self.modelTitle0
        elif self.modelIndex == 1:
            modelID = str(self.model1)
            model_title = self.modelTitle1
        elif self.modelIndex == 2:
            modelID = str(self.model2)
            model_title = self.modelTitle2
        elif self.modelIndex == 3:
            modelID = str(self.model3)
            model_title = self.modelTitle3
        elif self.modelIndex == 4:
            modelID = str(self.model4)
            model_title = self.modelTitle4
        elif self.modelIndex == 5:
            modelID = str(self.model5)
            model_title = self.modelTitle5
        elif self.modelIndex == 6:
            modelID = str(self.model6)
            model_title = self.modelTitle6
        elif self.modelIndex == 7:
            modelID = str(self.model7)
            model_title = self.modelTitle7
        """

        #self.modelId = str(self.modelId)
        #self.modelID = str(self.modelIDTest)
        #self.modelTitle = str(self.modelTitleTest)
        self.temp_dir = os.path.join(Config.THANGS_MODEL_DIR)
        print("Temp Directory: ", self.temp_dir)
        print("Model ID: ", self.modelId)
        print("Model Title: ", self.modelTitle)
        fileDownloaded = [item for item in _files_list if item[0] == self.modelId and item[1] == self.modelTitle]

        if len(fileDownloaded) < 1:
            headers = {"Authorization": "Bearer "+self.bearer,}
            print("URL: ", self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(self.modelId)+"/download-url")
            # TODO: Add in rate limit after this following request (Will error 429)
            try:
                response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(self.modelId)+"/download-url", headers=headers)
            except:
                if response.status_code == 429:
                    self.import_limit = True
                    self.importing = False
                    return
                elif response.status_code == 403:
                    self.refresh_bearer()
                    headers = {"Authorization": "Bearer "+self.bearer,}
                    try:
                        response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(self.modelId)+"/download-url", headers=headers) 
                    except:
                        self.importing = False
                        return
                self.importing = False
                return
            self.import_limit = False
            responseData = response.json()
            modelURL = responseData["downloadUrl"]

            if modelURL is None:
                print('Url is None')
                return

            r = requests.get(modelURL, stream=True)
                    
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
            self.file_path = os.path.join(self.temp_dir, filename)

            print("Starting Download")
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
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
                        print("filedata: ", done)

            _files_list.append(tuple((self.modelId, self.modelTitle, filename)))
            wm.progress_end()
        else:
            fileDownloaded = [item for item in _files_list if item[0] == self.modelId and item[1] ==  item[2]]

            if len(fileDownloaded) > 0:
                self.file_path = os.path.join(Config.THANGS_MODEL_DIR, self.modelTitle)
            else:
                fileDownloadedStl = [item for item in _files_list if item[0] == self.modelId and item[1] == self.modelTitle]
                self.file_path = os.path.join(Config.THANGS_MODEL_DIR, str(fileDownloadedStl[0][2]))

            split_tup_top = os.path.splitext(self.file_path)
            self.file_extension = split_tup_top[1]    
            print('Model Already Downloaded')

        #print("Callback")
        #if self.import_callback is not None:
        #    self.import_callback()
        
        self.run_in_main_thread(self.import_callback)

        # self.import_model()

    def import_model(self):
        print("Starting File Import")

        self.amplitude.send_amplitude_event("Thangs Blender Addon - import model", event_properties={
                    'extension': self.fileType,
                    'domain': self.domain,
                })

        try:
            if self.file_extension == '.zip' or self.file_extension == '.usdz':
                self.zipped_file_path = self.file_path
                if self.unzip_archive():
                    split_tup_top = os.path.splitext(self.modelTitle)
                    self.file_extension = split_tup_top[1]
                    self.file_path = os.path.join(self.temp_dir, self.modelTitle)
                else:
                    raise Exception("Unzipping didn't complete")
        except:
            print('Unzip error')
            self.importing = False
            return
        
        print("File Path: ", self.file_path)
        print("File Extension: ", self.file_extension)

        try:
            if self.file_extension == '.fbx':
                print('fbx import')
                bpy.ops.import_scene.fbx(filepath=self.file_path)
            elif self.file_extension == '.obj':
                print('obj import')
                bpy.ops.import_scene.obj(filepath=self.file_path)
            elif self.file_extension == '.glb' or self.file_extension == '.gltf':
                print('gltf + glb import')
                bpy.ops.import_scene.gltf(filepath=self.file_path, import_pack_images=True, merge_vertices=False, import_shading='NORMALS', guess_original_bind_pose=True, bone_heuristic='TEMPERANCE')
            elif self.file_extension == '.usd' or self.file_extension == '.usda' or self.file_extension == '.usdc':
                print('usdz import')
                bpy.ops.wm.usd_import(filepath=self.file_path, relative_path=True)
            else:
                print('stl import')
                bpy.ops.import_mesh.stl(filepath=self.file_path)
        except:
            print('Failed to Import')
            return
            
        print("Imported")

        self.importing = False
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
                fileUnarchived = [item for item in _files_list if item[2] == file]

                if len(fileUnarchived) < 1:
                    _files_list.append(tuple((self.modelId, self.modelTitle, file)))
            
            return True

        else:
            print('Archive doesn\'t exist')
            return False
