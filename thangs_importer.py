import webbrowser
import urllib.parse
import os
import time
import math
from urllib.request import urlopen
import tempfile
import urllib.request
import urllib.parse
import requests
import os
import importlib
import threading
import asyncio
# from . import addon_updater_ops
import socket
import json
import shutil
from .config import ThangsConfig, get_config
from uuid import UUID

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
        self.access_token = ''
        self.api_token = ''
        self.headers = {}
        self.username = ''
        self.thumbnails = []
        self.context = ""
        self.thangs_ui_mode = ''
        self.modelIds = []
        self.modelTitles = []
        self.filePaths = []
        self.modelInfo = []
        self.enumItems = []
        self.licenses = []
        self.creators = []
        self.filetype = []
        self.totalModels = 0
        self.Counter = 0
        self.pcoll = ""
        self.PageNumber = 1
        self.Directory = ""
        self.PageTotal = 0
        self.preview_collections = {}
        self.eventCall = ""
        self.CurrentPage = 1
        self.searching = False
        self.failed = False
        self.query = ""
        self.deviceId = ""
        self.ampURL = ''
        self.import_thread = None
        self.model_thread = None
        self.import_callback = callback
        self.model_path = ""
        self.uid = ""
        self.Thangs_Config = get_config()
        self.modelID = ""
        self.modelIndex = 0
        self.bearer = ""
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
        pass


    def handle_download(self, modelIndex):  # (self, r, *args, **kwargs):
        #    return
        self.modelIndex = modelIndex
        print("Before Archive Call")
        self.import_thread = threading.Thread(target=self.get_archive).start()
        return True

    def get_archive(self):
        print("Top of Archive")
        model_title = ""
        modelID = ""
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
    
        print(self.bearer)
        headers = {"Authorization": "Bearer "+self.bearer,}

        print(headers)
        print(self.Thangs_Config.thangs_config['url'])
        response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/parts/"+str(modelID)+"/download-url", headers=headers)
        print(response)
        print(response.status_code)
        responseData = response.json()
        modelURL = responseData["downloadUrl"]
        print(modelURL)
        if modelURL is None:
            print('Url is None')
            return

        r = requests.get(modelURL, stream=True)
        self.uid = str(model_title)
        temp_dir = os.path.join(Config.THANGS_MODEL_DIR, self.uid)

        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)


        print("Temp Dir: ", temp_dir)

        urlDecoded = urllib.parse.unquote(modelURL)
        print('urlDecoded', urlDecoded)

        split_tup_top = os.path.splitext(urlDecoded)
        file_extension = split_tup_top[1]
        file_extension = file_extension.replace('"', '')
        self.file_extension = file_extension.lower()
        print('file_extension: ', self.file_extension)

        fileindex = urlDecoded.rindex('filename="')
        filename = urlDecoded[-(len(urlDecoded) - (fileindex + 10)):]
        filename = filename.replace('"', '')
        print('filename: ', filename)

        file_path = os.path.join(temp_dir, filename)
        print("file path: ", file_path)

        if not os.path.exists(file_path):
            print("Starting Count")
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            with open(file_path, "wb") as f:
                total_length = r.headers.get('content-length')
                if total_length is None:  # no content length header
                    f.write(r.content)
                else:
                    dl = 0
                    total_length = int(total_length)
                    for data in r.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(100 * dl / total_length)
                        wm.progress_update(done)
                        print("filedata: ", done)

            wm.progress_end()
        else:
            print('Model already downloaded')

        self.file_path = file_path
        self.temp_dir = temp_dir
        self.import_model()
        return

    def unzip_archive(self):
        if os.path.exists(self.file_path):
            import zipfile
            try:
                print("zip archive_path: ", self.file_path)
                zip_ref = zipfile.ZipFile(self.file_path, 'r')
                extract_dir = os.path.dirname(self.file_path)
                print("zip extract_dir: ", extract_dir)
                zip_ref.extractall(extract_dir)
                zip_ref.close()
            except zipfile.BadZipFile:
                print('Error when dezipping file')
                #os.remove(archive_path)
                print('Invaild zip. Try again')
                return None, None

            files = os.listdir(extract_dir)
            files = [f for f in files if os.path.isfile(extract_dir + '/' + f)]
            print(*files, sep="\n")

            for file in files:
                if file.endswith(".gltf") or file.endswith(".usd") or file.endswith(".usda") or file.endswith(".usdc"):
                    unzipped_file_path = os.path.join(extract_dir, file)
                    split_tup_top = os.path.splitext(file)
                    unzipped_file_extension = split_tup_top[1]
                    break

            print("zip unzipped_file_path: ", unzipped_file_path)
            print("zip unzipped_file_extension: ", unzipped_file_extension)
            return unzipped_file_path, unzipped_file_extension

        else:
            print('ERROR: archive doesn\'t exist')

    def import_model(self):
        print("Starting File Import")
        print("self.file_path: ", self.file_path)

        try:
            if self.file_extension == '.zip' or self.file_extension == '.usdz':
                unzipped_file_path, unzipped_file_extension = self.unzip_archive()
                self.file_path = unzipped_file_path
                self.file_extension = unzipped_file_extension
        except:
            print('unzip error')

        print("self.file_path: ", self.file_path)
        print("self.file_extension: ", self.file_extension)
        
        try:
            if self.file_extension == '.fbx':
                print('fbx')
                bpy.ops.import_scene.fbx(filepath=self.file_path)
            elif self.file_extension == '.obj':
                print('obj')
                bpy.ops.import_scene.obj(filepath=self.file_path)
            elif self.file_extension == '.glb' or self.file_extension == '.gltf':
                print('gltf + glb import')
                bpy.ops.import_scene.gltf(filepath=self.file_path, import_pack_images=True, merge_vertices=False, import_shading='NORMALS', guess_original_bind_pose=True, bone_heuristic='TEMPERANCE')
            elif self.file_extension == '.usd' or self.file_extension == '.usda' or self.file_extension == '.usdc':
                print('usdz import')
                bpy.ops.wm.usd_import(filepath=self.file_path, relative_path=True)
            else:
                print('stl')
                bpy.ops.import_mesh.stl(filepath=self.file_path)
        except:
            print('import error')
            
        print("Imported")
        Utils.clean_downloaded_model_dir(self.temp_dir)
        print("Cleaned")
        #root_name = modelTitle
        # Utils.clean_node_hierarchy(
        #    [o for o in bpy.data.objects if o.name not in old_objects], root_name)
        #print("Cleaned Nodes")
        return
