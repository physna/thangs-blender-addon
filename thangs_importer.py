import webbrowser
import urllib.parse
import os
import time
import math
from urllib.request import urlopen
import tempfile
import urllib.request
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


def initialize_thangsAPI(callback):
    global _thangs_api
    _thangs_api = ThangsApi(callback)

class Config:
    THANGS_MODEL_DIR = ""


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
        self.gltf_path = ""
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

    # def download_model(self):
    #        download_url = ""
    #        requests.get(download_url, headers=self.headers, hooks={'response': self.handle_download})

    def handle_download(self, modelIndex):  # (self, r, *args, **kwargs):
        # if r.status_code != 200 or 'stl' not in r.json():
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

        print("Temp Dir")
        print(temp_dir)
        # archive_path = os.path.join(temp_dir, '{}.zip'.format(uid))
        archive_path = os.path.join(temp_dir, '{}.stl'.format(self.uid))
        print("Arch Path")
        print(archive_path)
        if not os.path.exists(archive_path):
            print("Starting Count")
            wm = bpy.context.window_manager
            wm.progress_begin(0, 100)
            with open(archive_path, "wb") as f:
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

            wm.progress_end()
        else:
            print('Model already downloaded')

        # gltf_path, gltf_zip = unzip_archive(archive_path)
        self.gltf_path = archive_path
        self.import_model()
        return
        if self.gltf_path:
            try:
                print("Starting Import Thread")
                # self.import_thread = threading.Thread(
                #    target=self.import_model).start()
                self.import_model()
                # import_model(gltf_path, uid)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
        else:
            print("ERROR", "Download error",
                  "Failed to download model (url might be invalid)")
        return

    def unzip_archive(self, archive_path):
        if os.path.exists(archive_path):
            import zipfile
            try:
                zip_ref = zipfile.ZipFile(archive_path, 'r')
                extract_dir = os.path.dirname(archive_path)
                zip_ref.extractall(extract_dir)
                zip_ref.close()
            except zipfile.BadZipFile:
                print('Error when dezipping file')
                os.remove(archive_path)
                print('Invaild zip. Try again')
                return None, None

            stl_file = os.path.join(extract_dir, 'scene.gltf')
            return stl_file, archive_path

        else:
            print('ERROR: archive doesn\'t exist')

    def import_model(self):
        #old_objects = [o.name for o in bpy.data.objects]
        print("Starting File Import")
        bpy.ops.import_mesh.stl(filepath=self.gltf_path)
        print("Imported")
        Utils.clean_downloaded_model_dir(self.uid)
        print("Cleaned")
        # print("Imported")
        #root_name = modelTitle
        # Utils.clean_node_hierarchy(
        #    [o for o in bpy.data.objects if o.name not in old_objects], root_name)
        #print("Cleaned Nodes")
        return
