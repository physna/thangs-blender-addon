import threading
import configparser
from pathlib import Path
import json
import base64
import requests
from requests.adapters import HTTPAdapter, Retry
from requests import Session, exceptions
import uuid
from urllib.request import urlopen
import urllib.request
import urllib.parse
import threading
import os
import shutil
import math
import platform
from requests.exceptions import Timeout

from .model_info import ModelInfo
from .fp_val import FP
from .thangs_events import ThangsEvents
from .config import get_config, ThangsConfig
from .thangs_importer import ThangsApi, initialize_thangs_api, get_thangs_api, Utils, Config
import bpy
import ssl
import socket
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
import socket


class ThangsFetcher():
    def __init__(self, callback=None):
        self.search_thread = None
        self.search_callback = callback
        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""
        self.uuid = ""
        self.bearer = ""

        self.models = []
        # self.enumModels1 = []
        # self.enumModels2 = []
        # self.enumModels3 = []
        # self.enumModels4 = []
        # self.enumModels5 = []
        # self.enumModels6 = []
        # self.enumModels7 = []
        # self.enumModels8 = []

        # self.enumModelInfo = []
        # self.enumModelTotal = []
        # self.thumbnailNumbers = []

        self.preview_collections = {}
        self.searchMetaData = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1
        # self.result1 = 0
        # self.result2 = 0
        # self.result3 = 0
        # self.result4 = 0
        # self.result5 = 0
        # self.result6 = 0
        # self.result7 = 0
        # self.result8 = 0

        self.searching = False
        self.selectionSearching = False
        self.failed = False
        self.newSearch = False
        self.SelectionFailed = False

        self.Thangs_Config = ThangsConfig()
        self.Thangs_Utils = Utils()
        self.Config = Config()
        self.amplitude = ThangsEvents()
        self.amplitude.deviceId = socket.gethostname().split(".")[0]
        self.amplitude.deviceOs = platform.system()
        self.amplitude.deviceVer = platform.release()
        self.FP = FP()
        self.thangs_api = get_thangs_api()
        self.modelsCopy = []
        self.modelList = []

        pass

    class PartStruct():
        def __init__(self, partId, partFileName, fileType, iconId, domain, index):
            self.partId = partId
            self.partFileName = partFileName
            self.iconId = iconId
            self.fileType= fileType
            self.index = index
            self.domain = domain
            pass

        def getID(self):
            return str(self.partId)

    class ModelStruct():
        def __init__(self, partList):
            self.partSelected = 0
            self.parts = partList
            pass

    def reset(self):
        self.search_thread = None
        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""
        self.uuid = ""

        self.models = []
        self.enumModels1 = []
        self.enumModels2 = []
        self.enumModels3 = []
        self.enumModels4 = []
        self.enumModels5 = []
        self.enumModels6 = []
        self.enumModels7 = []
        self.enumModels8 = []

        self.enumModelInfo = []
        self.enumModelTotal = []
        #self.thumbnailNumbers = []

        self.preview_collections = {}
        self.searchMetaData = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1
        self.result1 = 0
        self.result2 = 0
        self.result3 = 0
        self.result4 = 0
        self.result5 = 0
        self.result6 = 0
        self.result7 = 0
        self.result8 = 0

        self.searching = False
        self.failed = False
        self.newSearch = False

        pass

    def search(self, query):
        if self.searching:
            return False
        self.query = urllib.parse.quote(query)
        # this should return immediately with True
        # kick off a thread that does the searching
        self.search_thread = threading.Thread(
            target=self.get_http_search).start()
        return True

    def selectionSearch(self, context):
        if self.searching or self.selectionSearching:
            return False
        act_obj = bpy.context.active_object
        if act_obj:
            previous_mode = act_obj.mode  # Keep current mode
            # Keep already created
            previous_objects = set(context.scene.objects)
            temp_dir = os.path.join(
                self.Config.THANGS_MODEL_DIR, "ThangsSelectionSearch")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            print(temp_dir)

            try:
                if act_obj.mode == "EDIT":
                    bpy.ops.mesh.duplicate_move()
                    bpy.ops.mesh.fill(use_beauty=True)
                    bpy.ops.mesh.separate(type='SELECTED')

        #            #Back to object mode
                    bpy.ops.object.mode_set(mode='OBJECT')

                    bpy.context.active_object.select_set(False)

                    new_object = next(
                        o for o in context.scene.objects if o not in previous_objects)
                    new_object.update_from_editmode()  # Ensure internal data are ok

                    context.view_layer.objects.active = new_object

                    print(bpy.context.active_object)
                    #archive_path = os.path.join(temp_dir, '{}.stl'.format(self.uid))
                    path = Path("D:\Github")
                    stl_path = path / f"blender_selection.stl"
                    print(stl_path)
                    bpy.ops.export_mesh.stl(
                        filepath=str(stl_path),
                        use_selection=True)

                else:
                    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked": False, "mode": 'TRANSLATION'}, TRANSFORM_OT_translate={"value": (0, 0, 0), "orient_axis_ortho": 'X', "orient_type": 'GLOBAL', "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type": 'GLOBAL', "constraint_axis": (False, False, False), "mirror": False, "use_proportional_edit": False, "proportional_edit_falloff": 'SMOOTH', "proportional_size": 1,
                                                                                                                                        "use_proportional_connected": False, "use_proportional_projected": False, "snap": False, "snap_target": 'CLOSEST', "snap_point": (0, 0, 0), "snap_align": False, "snap_normal": (0, 0, 0), "gpencil_strokes": False, "cursor_transform": False, "texture_space": False, "remove_on_cancel": False, "view2d_edge_pan": False, "release_confirm": False, "use_accurate": False, "use_automerge_and_split": False})
                    new_object = next(
                        o for o in context.scene.objects if o not in previous_objects)
                    new_object.update_from_editmode()

                    context.view_layer.objects.active = new_object
                    path = Path(temp_dir)
                    stl_path = path / f"blender_selection.stl"
                    bpy.ops.export_mesh.stl(
                        filepath=str(stl_path),
                        use_selection=True)

                    print(stl_path)
                    print(bpy.context.active_object)
                    context.view_layer.objects.active = new_object

                bpy.ops.object.delete()

                self.search_thread = threading.Thread(
                    target=self.get_stl_search, args=(stl_path,)).start()

            except:
                bpy.ops.object.mode_set(mode=previous_mode)
                pass

        return True

    def cancel(self):
        if self.search_thread is not None:
            self.search_thread.terminate()
            self.search_thread = None
            self.searching = False
            self.selectionSearching = False
            self.failed = False
            self.newSearch = False
            self.reset
            return True
        return False

    def get_total_results(self, response):
        if response.status_code != 200:
            self.totalModels = 0
            self.PageTotal = 0
        else:
            print("Started Counting Results")
            responseData = response.json()
            items = responseData["searchMetadata"]
            self.totalModels = items['totalResults']
            if math.ceil(self.totalModels/8) > 99:
                self.PageTotal = 99
            else:
                self.PageTotal = math.ceil(self.totalModels/8)

            if items['totalResults'] == 0:
                self.amplitude.send_amplitude_event("Text search - No Results", event_properties={
                    'searchTerm': items['originalQuery'],
                    'searchId': self.uuid,
                    'numOfMatches': items['totalResults'],
                    'pageCount': items['page'],
                    'searchMetadata': self.searchMetaData,
                })
            else:
                self.amplitude.send_amplitude_event("Text search - Results", event_properties={
                    'searchTerm': items['originalQuery'],
                    'searchId': self.uuid,
                    'numOfMatches': items['totalResults'],
                    'pageCount': items['page'],
                    'searchMetadata': self.searchMetaData,
                })

    def get_stl_results(self, response):
        if response.status_code != 200:
            self.totalModels = 0
            self.PageTotal = 0
        else:
            print("Started Counting Results")
            responseData = response.json()
            self.totalModels = responseData["numMatches"]
            if math.ceil(self.totalModels/8) > 99:
                self.PageTotal = 99
            else:
                self.PageTotal = math.ceil(self.totalModels/8)
        # Add in event Code

    def get_lazy_thumbs(self, I, X, thumbnail, modelID,):
        try:
            print(f'Fetching part {thumbnail}')
            filePath = urllib.request.urlretrieve(thumbnail)
            filepath = os.path.join(modelID, filePath[0])
        except:
            filePath = Path(__file__ + "\icons\placeholder.png")
            filepath = os.path.join(modelID, filePath)

        try:
            thumb = self.pcoll.load(modelID, filepath, 'IMAGE')
        except:
            thumb = self.pcoll.load(modelID+str(X), filepath, 'IMAGE')

        try:
            self.modelList[I].parts[X].iconId = thumb.icon_id
        except:
            print("Thumbnail Doesn't Exist")

    def get_http_search(self):
        global thangs_config
        # Clean up temporary files from previous attempts
        urllib.request.urlcleanup()
        print("Started Search")
        self.searching = True
        self.failed = False

        self.Directory = self.query
        # Added
        self.CurrentPage = self.PageNumber

        self.amplitude.send_amplitude_event("Text Search Started", event_properties={
            'searchTerm': self.query,
        })

        # Get the preview collection (defined in register func).
        self.pcoll = self.preview_collections["main"]

        if self.CurrentPage == self.pcoll.Model_page:
            if self.Directory == self.pcoll.Model_dir:
                self.searching = False
                self.search_callback()
                return
            else:
                self.newSearch = True
                self.PageNumber = 1
                self.CurrentPage = 1

        if self.Directory == "" or self.Directory.isspace():
            self.searching = False
            self.search_callback()
            return

        self.models.clear()

        self.Directory = self.query
        self.CurrentPage = self.PageNumber

        # Get the preview collection (defined in register func).
        self.pcoll = self.preview_collections["main"]

        for pcoll in self.preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        self.preview_collections.clear()

        self.pcoll = bpy.utils.previews.new()
        self.pcoll.Model_dir = ""
        self.pcoll.Model = ()
        self.pcoll.Model_page = self.CurrentPage

        self.preview_collections["main"] = self.pcoll

        self.pcoll = self.preview_collections["main"]

        if self.newSearch == True:
            try:
                response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/v2/search-by-text?page="+str(self.CurrentPage-1)+"&searchTerm="+self.query +
                                        "&pageSize=8&collapse=true",
                                        headers={"x-fp-val": self.FP.getVal(self.Thangs_Config.thangs_config['url']+"fp_m")})
            except:
                self.failed = True
                self.newSearch = False
                self.searching = False
                return
        else:
            try:
                response = requests.get(
                    str(self.Thangs_Config.thangs_config['url'])+"api/models/v2/search-by-text?page=" +
                    str(self.CurrentPage-1)+"&searchTerm="+self.query +
                    "&pageSize=8&collapse=true",
                    headers={"x-thangs-searchmetadata": base64.b64encode(
                        json.dumps(self.searchMetaData).encode()).decode(),
                        "x-fp-val": self.FP.getVal(self.Thangs_Config.thangs_config['url']+"fp_m")},
                )
            except:
                self.failed = True
                self.newSearch = False
                self.searching = False
                return

        if response.status_code != 200:
            self.amplitude.send_amplitude_event("Text Search - Failed", event_properties={
                'searchTerm': self.query,
            })

        else:
            responseData = response.json()
            items = responseData["results"]
            if self.newSearch == True:
                self.uuid = str(uuid.uuid4())
                self.searchMetaData = responseData["searchMetadata"]
                self.searchMetaData['searchID'] = self.uuid
                data = {
                    "searchId": self.uuid,
                    "searchTerm": self.query,
                }

                self.amplitude.send_thangs_event("Capture", data)

            self.get_total_results(response)

            # ugh
            old_context = ssl._create_default_https_context
            ssl._create_default_https_context = ssl._create_unverified_context

            self.modelList.clear()
            I = 0
            for item in items:
                self.modelsCopy.clear()

                if len(item["thumbnails"]) > 0:
                    thumbnail = item["thumbnails"][0]
                else:
                    thumbnail = item["thumbnailUrl"]

                self.models.append(ModelInfo(
                    item["modelId"],
                    item["modelTitle"],
                    item['attributionUrl'],
                    item["ownerUsername"],
                    item["license"],
                    item["domain"],
                    item["scope"],
                    item["originalFileType"],
                    (((self.CurrentPage - 1) * 8) + I)
                ))

                try:
                    print(f'Fetching {thumbnail}')
                    filePath = urllib.request.urlretrieve(thumbnail)
                    filepath = os.path.join(item["modelId"], filePath[0])
                except:
                    filePath = Path(__file__ + "\icons\placeholder.png")
                    filepath = os.path.join(item["modelId"], filePath)

                try:
                    thumb = self.pcoll.load(item["modelId"], filepath, 'IMAGE')
                except:
                    thumb = self.pcoll.load(
                        item["modelId"]+str(I), filepath, 'IMAGE')

                self.modelsCopy.append(self.PartStruct(item["modelId"], item["modelTitle"], item["originalFileType"], thumb.icon_id, item["domain"], 0))

                if len(item["parts"]) > 0:
                    parts = item["parts"]
                    X = 1
                    for part in parts:
                        print("Getting Thumbnail for {0}".format(part["modelId"]))
                        self.modelsCopy.append(self.PartStruct(
                                    part["modelId"], part["modelFileName"], part["originalFileType"], "", part["domain"], X))
                        
                        thumb_thread = threading.Thread(target=self.get_lazy_thumbs, args=(
                            I, X, part["thumbnailUrl"], part["modelId"],)).start()

                        X = X + 1

                self.modelList.append(self.ModelStruct(partList=self.modelsCopy[:]))

                I = I + 1

        try:
            ssl._create_default_https_context = old_context
        except:
            self.failed = True
            self.newSearch = False
            self.searching = False
            return

        self.pcoll.Model = self.models
        self.pcoll.Model_dir = self.Directory
        self.pcoll.Model_page = self.CurrentPage

        self.searching = False
        self.newSearch = False

        self.thangs_ui_mode = 'VIEW'

        if self.search_callback is not None:
            self.search_callback()

        print("Search Completed!")
        return

    def get_stl_search(self, stl_path):
        import re
        global thangs_config
        print("Started STL Search")
        self.selectionSearching = True

        self.CurrentPage = self.PageNumber

        self.pcoll = self.preview_collections["main"]

        self.models.clear()

        self.Directory = self.query
        self.CurrentPage = self.PageNumber

        # Get the preview collection (defined in register func).
        self.pcoll = self.preview_collections["main"]

        # Added

        for pcoll in self.preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        self.preview_collections.clear()

        self.pcoll = bpy.utils.previews.new()
        self.pcoll.Model_dir = ""
        self.pcoll.Model = ()
        # self.pcoll.ModelView1 = ()
        # self.pcoll.ModelView2 = ()
        # self.pcoll.ModelView3 = ()
        # self.pcoll.ModelView4 = ()
        # self.pcoll.ModelView5 = ()
        # self.pcoll.ModelView6 = ()
        # self.pcoll.ModelView7 = ()
        # self.pcoll.ModelView8 = ()
        self.pcoll.Model_page = self.CurrentPage

        self.preview_collections["main"] = self.pcoll

        self.pcoll = self.preview_collections["main"]

        headers = {
            "Authorization": "Bearer "+self.bearer,
        }

        try:
            response = requests.get(str(
                self.Thangs_Config.thangs_config['url'])+"api/search/v1/mesh-url?filename=mesh.stl", headers=headers)
            responseData = response.json()

            print(responseData)
        except:
            print("URL BROKEN")

        signedUrl = responseData["signedUrl"]
        new_Filename = responseData["newFileName"]

        data = open(stl_path, 'rb').read()

        print("Starting to Clean")
        shutil.rmtree(os.path.join(
            self.Config.THANGS_MODEL_DIR, "ThangsSelectionSearch"))
        print("Cleaned STL")

        s = requests.Session()

        retries = Retry(total=10,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504, 521],
                        allowed_methods=frozenset(['GET', 'POST', 'PUT']),)
        s.mount('https://', HTTPAdapter(max_retries=retries))

        try:
            s.put(url=signedUrl, data=data)  # params={'data': data}, args=(),
            #response = s.post(url, headers=headers, data=data)
        except:
            print("API Failed")
            self.selectionSearching = False
            self.searching = False
            self.newSearch = False
            self.SelectionFailed = True
            return

        print("Select Search Returned")

        try:
            url_filepath = urllib.parse.quote(new_Filename, safe='')
            url = str(
                self.Thangs_Config.thangs_config['url']+"api/search/v1/mesh-search?filepath="+url_filepath)
            print(url)
            response = requests.get(url=url, headers=headers)
            print(response.status_code())
            responseData = response.json()

            print(responseData)
        except:
            print("It BROKE")
            self.selectionSearching = False
            self.searching = False
            self.newSearch = False
            self.SelectionFailed = True
            return

        # if os.path.isfile(stl_path):
        #    os.remove(stl_path)
        # self.Thangs_Utils.clean_downloaded_model_dir("ThangsSelectionSearch")
        numMatches = responseData["numMatches"]
        items = responseData["matches"]

        # if self.newSearch == True:
        #     self.uuid = str(uuid.uuid4())
        #     self.searchMetaData = responseData["searchMetadata"]
        #     self.searchMetaData['searchID'] = self.uuid
        #     data = {
        #         "searchId": self.uuid,
        #         "searchTerm": self.query,
        #     }blender

        #self.amplitude.send_thangs_event("Capture", data)

        self.get_stl_results(response)

        self.i = 0

        # print(items)

        for item in items:
            print("--------")
            print("--------")
            print(item)
            self.enumModelInfo.clear()

            thumbnailAPIURL = item["thumbnail_url"]
            thumbnailURL = requests.head(thumbnailAPIURL)
            thumbnail = thumbnailURL.headers["Location"]

            modelTitle = item["title"]
            modelId = item["model_id"]

            self.models.append(
                ModelInfo(
                    modelId,
                    modelTitle,
                    str("https://thangs.com/m/") + item["external_id"],
                    "",
                    "",
                    "",
                    "",
                    "",
                    (((self.CurrentPage - 1) * 8) + self.i)
                )
            )

            thumbnail = thumbnail.replace("https", "http", 1)
            try:
                filePath = urllib.request.urlretrieve(thumbnail)
                filepath = os.path.join(modelId, filePath[0])
            except:
                filePath = Path(__file__ + "\icons\placeholder.png")
                filepath = os.path.join(modelId, filePath)

            thumb = self.pcoll.load(modelId, filepath, 'IMAGE')

            #self.thumbnailNumbers.append(thumb.icon_id)

            z = 0

            self.enumModelInfo.append(
                (modelId, modelTitle, ""))  # , z))

            if self.i == 0:
                self.enumModels1.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model0 = modelId
                self.thangs_api.modelTitle0 = modelTitle

            elif self.i == 1:
                self.enumModels2.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model1 = modelId
                self.thangs_api.modelTitle1 = modelTitle

            elif self.i == 2:
                self.enumModels3.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model2 = modelId
                self.thangs_api.modelTitle2 = modelTitle

            elif self.i == 3:
                self.enumModels4.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model3 = modelId
                self.thangs_api.modelTitle3 = modelTitle

            elif self.i == 4:
                self.enumModels5.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model4 = modelId
                self.thangs_api.modelTitle4 = modelTitle

            elif self.i == 5:
                self.enumModels6.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model5 = modelId
                self.thangs_api.modelTitle5 = modelTitle

            elif self.i == 6:
                self.enumModels7.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model6 = modelId
                self.thangs_api.modelTitle6 = modelTitle

            else:
                self.enumModels8.append(
                    (modelId, modelTitle, "", thumb.icon_id, z))
                self.thangs_api.model7 = modelId
                self.thangs_api.modelTitle7 = modelTitle

            self.enumModelTotal.append(self.enumModelInfo[:])
            self.i = self.i + 1

        if self.enumModels1:
            self.result1 = self.enumModels1[0][3]
        if self.enumModels2:
            self.result2 = self.enumModels2[0][3]
        if self.enumModels3:
            self.result3 = self.enumModels3[0][3]
        if self.enumModels4:
            self.result4 = self.enumModels4[0][3]
        if self.enumModels5:
            self.result5 = self.enumModels5[0][3]
        if self.enumModels6:
            self.result6 = self.enumModels6[0][3]
        if self.enumModels7:
            self.result7 = self.enumModels7[0][3]
        if self.enumModels8:
            self.result8 = self.enumModels8[0][3]

        self.pcoll.Model = self.models
        self.pcoll.ModelView1 = self.enumModels1
        self.pcoll.ModelView2 = self.enumModels2
        self.pcoll.ModelView3 = self.enumModels3
        self.pcoll.ModelView4 = self.enumModels4
        self.pcoll.ModelView5 = self.enumModels5
        self.pcoll.ModelView6 = self.enumModels6
        self.pcoll.ModelView7 = self.enumModels7
        self.pcoll.ModelView8 = self.enumModels8
        self.pcoll.Model_dir = self.Directory
        # Added

        self.pcoll.Model_page = self.CurrentPage

        self.selectionSearching = False
        self.searching = False
        self.newSearch = False

        self.thangs_ui_mode = 'VIEW'

        print("Callback")
        if self.search_callback is not None:
            self.search_callback()

        print("Selection Search Completed!")

        return
