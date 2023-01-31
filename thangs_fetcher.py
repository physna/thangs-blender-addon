import bpy
import threading
import json
import base64
import requests
import uuid
import urllib.request
import urllib.parse
import threading
import os
import math
import platform
import ssl
import socket
import time

from .model_info import ModelInfo
from .thangs_events import ThangsEvents
from .config import ThangsConfig
from .thangs_importer import get_thangs_api, Utils, Config
from pathlib import Path
from requests.adapters import HTTPAdapter, Retry


class ThangsFetcher():
    def __init__(self, callback=None, results_to_show=8, stl_callback=None):
        self.search_thread = None
        self.search_callback = callback
        self.stl_callback = stl_callback

        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""
        self.uuid = ""
        self.bearer = ""
        self.searchType = ""

        self.models = []
        self.partList = []
        self.modelList = []

        self.preview_collections = {}
        self.searchMetaData = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1

        self.searching = False
        self.selectionSearching = False
        self.failed = False
        self.newSearch = False
        self.selectionFailed = False
        self.selectionEmpty = False
        self.selectionThumbnailGrab = False

        self.Thangs_Config = ThangsConfig()
        self.Thangs_Utils = Utils()
        self.Config = Config()
        self.amplitude = ThangsEvents()
        self.amplitude.deviceId = socket.gethostname().split(".")[0]
        self.amplitude.deviceOs = platform.system()
        self.amplitude.deviceVer = platform.release()
        self.thangs_api = get_thangs_api()
        self.results_to_show = results_to_show
        pass

    class PartStruct():
        def __init__(self, partId, partFileName, fileType, iconId, domain, index):
            self.partId = partId
            self.partFileName = partFileName
            self.iconId = iconId
            self.fileType = fileType
            self.index = index
            self.domain = domain
            pass

        def getID(self):
            return str(self.partId)

    class ModelStruct():
        def __init__(self, modelTitle, partList):
            self.partSelected = 0
            self.modelTitle = modelTitle
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
        self.bearer = ""

        self.models = []
        self.partList = []
        self.modelList = []

        self.preview_collections = {}
        self.searchMetaData = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1

        self.searching = False
        self.selectionSearching = False
        self.failed = False
        self.newSearch = False
        self.selectionFailed = False
        pass

    def search(self, query):
        if self.searching:
            return False
        self.query = query
        # this should return immediately with True
        # kick off a thread that does the searching
        self.search_thread = threading.Thread(
            target=self.get_http_search).start()
        return True

    def selectionSearch(self, context):
        if self.searching or self.selectionSearching:
            return False
        self.selectionSearching = True

        self.thangs_ui_mode = 'SEARCH'
        self.stl_callback()

        act_obj = bpy.context.active_object
        temp_dir = os.path.join(
            self.Config.THANGS_MODEL_DIR, "ThangsSelectionSearch")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        if act_obj:
            previous_mode = act_obj.mode  # Keep current mode
            # Keep already created
            previous_objects = set(context.scene.objects)

            try:
                if act_obj.mode == "EDIT":
                    print("Searching Edit")
                    bpy.ops.mesh.duplicate_move()
                    bpy.ops.mesh.solidify()
                    bpy.ops.mesh.separate(type='SELECTED')

                    # Back to object mode
                    bpy.ops.object.mode_set(mode='OBJECT')

                    bpy.context.active_object.select_set(False)

                    new_object = next(
                        o for o in context.scene.objects if o not in previous_objects)
                    new_object.update_from_editmode()  # Ensure internal data are ok

                    context.view_layer.objects.active = new_object

                    print(bpy.context.active_object)
                    #archive_path = os.path.join(temp_dir, '{}.stl'.format(self.uid))
                    path = Path(temp_dir)
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

                return stl_path

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

    def get_total_results(self, searchMetadata):

        print("Started Counting Results")
        items = searchMetadata
        self.totalModels = items['totalResults']
        pageTotal = math.ceil(self.totalModels/self.results_to_show)
        if pageTotal > 99:
            self.PageTotal = 99
        else:
            self.PageTotal = pageTotal

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

    def get_stl_results(self, items):
        print("Started Counting Results")
        self.totalModels = len(items)
        pageTotal = math.ceil(self.totalModels/self.results_to_show)
        if pageTotal > 99:
            self.PageTotal = 99
        else:
            self.PageTotal = pageTotal
        # Add in event Code

    def get_lazy_thumbs(self, I, X, thumbnail, modelID, temp_dir,):
        icon_path = os.path.join(temp_dir, modelID)
        if not os.path.exists(icon_path):
            os.makedirs(icon_path)

        thumbnailPath = thumbnail.replace("%2F", "/").replace("?", "/")
        icon_path = os.path.join(icon_path, thumbnailPath.split('/')[-1])

        if not os.path.exists(icon_path):
            try:
                print(f'Fetching {thumbnail}')
                filePath = urllib.request.urlretrieve(thumbnail, icon_path)
                icon_path = os.path.join(modelID, filePath[0])
            except Exception as e:
                print(e)
                filePath = Path(__file__ + "\icons\placeholder.png")
                icon_path = os.path.join(modelID, filePath)

        try:
            thumb = self.pcoll.load(modelID, icon_path, 'IMAGE')
        except:
            thumb = self.pcoll.load(modelID+str(X), icon_path, 'IMAGE')

        try:
            time.sleep(.25)
            self.modelList[I].parts[X].iconId = thumb.icon_id
        except Exception as e:
            print(e + f" on Image {X}")

    def display_search_results(self, responseData, show_summary=True):
        temp_dir = os.path.join(
            self.Config.THANGS_MODEL_DIR, "ThangsSearchIcons")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

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
        if show_summary:
            self.get_total_results(responseData["searchMetadata"])

        # ugh
        old_context = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context

        self.modelList.clear()
        I = 0
        if self.searchType == "object":
            self.selectionThumbnailGrab = True
            self.stl_callback()
        for item in items:
            self.partList.clear()

            if len(item["thumbnails"]) > 0:
                thumbnail = item["thumbnails"][0]
            else:
                thumbnail = item["thumbnailUrl"]

            #thumbnail = f"https://thangs-thumbs-dot-gcp-and-physna.uc.r.appspot.com/convert/{model_id}.stl?source=phyndexer-production-headless-bucket"

            self.models.append(ModelInfo(
                item["modelId"],
                item.get('modelTitle') or item.get('modelFileName'),
                item['attributionUrl'],
                item["ownerUsername"],
                item["license"],
                item["domain"],
                item["scope"],
                item.get("originalFileType"),
                (((self.CurrentPage - 1) * 8) + I)
            ))

            icon_path = os.path.join(temp_dir, item["modelId"])
            if not os.path.exists(icon_path):
                os.makedirs(icon_path)
            thumbnailPath = thumbnail.replace("%2F", "/").replace("?", "/")
            icon_path = os.path.join(icon_path, thumbnailPath.split('/')[-1])
            if not os.path.exists(icon_path):
                try:
                    print(f'Fetching {thumbnail}')
                    filePath = urllib.request.urlretrieve(thumbnail, icon_path)
                    icon_path = os.path.join(item["modelId"], filePath[0])
                except Exception as e:
                    print(e)
                    filePath = Path(__file__ + "\icons\placeholder.png")
                    icon_path = os.path.join(item["modelId"], filePath)

            try:
                thumb = self.pcoll.load(item["modelId"], icon_path, 'IMAGE')
            except:
                thumb = self.pcoll.load(
                    item["modelId"]+str(I), icon_path, 'IMAGE')

            self.partList.append(self.PartStruct(item["modelId"], item["modelFileName"], item.get(
                "originalFileType"), thumb.icon_id, item["domain"], 0))

            if len(item["parts"]) > 0:
                parts = item["parts"]
                X = 1
                for part in parts:
                    print("Getting Thumbnail for {0}".format(part["modelId"]))
                    self.partList.append(self.PartStruct(
                        part["modelId"], part["modelFileName"], part.get("originalFileType"), "", part["domain"], X))

                    thumb_thread = threading.Thread(target=self.get_lazy_thumbs, args=(
                        I, X, part["thumbnailUrl"], part["modelId"], temp_dir,)).start()

                    X += 1

            title = item.get('modelTitle') or item.get('modelFileName')
            self.modelList.append(self.ModelStruct(
                modelTitle=title, partList=self.partList[:]))

            I += 1

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
        self.selectionSearching = False
        self.newSearch = False
        self.selectionThumbnailGrab = False

        self.thangs_ui_mode = 'VIEW'

        if self.search_callback is not None:
            self.search_callback()

        print("Search Completed!")

    def get_http_search(self):
        try:
            self.searchType = "Text"
            # Clean up temporary files from previous attempts
            urllib.request.urlcleanup()
            print("Started Search")
            self.searching = True
            self.failed = False

            self.Directory = self.query
            # Added
            self.CurrentPage = self.PageNumber

            # Get the preview collection (defined in register func).
            self.pcoll = self.preview_collections["main"]

            if self.CurrentPage == self.pcoll.Model_page:
                if self.Directory == self.pcoll.Model_dir:
                    self.searching = False
                    self.search_callback()
                    return
                else:
                    self.amplitude.send_amplitude_event("Text Search Started", event_properties={
                        'searchTerm': self.query,
                    })
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
                    response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/v2/search-by-text?page="+str(self.CurrentPage-1)+"&searchTerm=" + str(urllib.parse.quote(self.query, safe='')) +
                                            "&pageSize="+str(self.results_to_show)+"&collapse=true")
                except Exception as e:
                    print(e)
                    self.failed = True
                    self.newSearch = False
                    self.searching = False
                    return
            else:
                try:
                    response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/v2/search-by-text?page="+str(self.CurrentPage-1)+"&searchTerm="+str(urllib.parse.quote(self.query, safe='')) +
                                            "&pageSize=" +
                                            str(self.results_to_show) +
                                            "&collapse=true",
                                            headers={"x-thangs-searchmetadata": base64.b64encode(
                                                json.dumps(self.searchMetaData).encode()).decode()},
                                            )
                except Exception as e:
                    print(e)
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
                self.display_search_results(responseData)
            return

        except Exception as e:
            print(e)
            self.failed = True
            self.newSearch = False
            self.searching = False
            self.search_callback
            return None

    def display_stl_results(self, responseData, show_summary=True):
        temp_dir = os.path.join(
            self.Config.THANGS_MODEL_DIR, "ThangsSearchIcons")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        items = responseData["results"]
        if self.newSearch == True:
            self.uuid = str(uuid.uuid4())
            self.searchMetaData = responseData["searchMetadata"]
            self.searchMetaData['searchID'] = self.uuid
            data = {
                "searchId": self.uuid,
                "searchTerm": "Selection Search",
            }

            self.amplitude.send_thangs_event("Capture", data)
        if show_summary:
            self.get_stl_results(items)

        # ugh
        old_context = ssl._create_default_https_context
        ssl._create_default_https_context = ssl._create_unverified_context

        self.modelList.clear()
        I = 0
        if self.searchType == "object":
            self.selectionThumbnailGrab = True
            self.stl_callback()
        for item in items[((self.CurrentPage-1)*8):(self.CurrentPage*8)]:
            self.partList.clear()

            if len(item["thumbnails"]) > 0:
                thumbnail = item["thumbnails"][0]
            else:
                thumbnail = item["thumbnailUrl"]

            self.models.append(ModelInfo(
                item["modelId"],
                item.get('modelTitle') or item.get('modelFileName'),
                item['attributionUrl'],
                item["ownerUsername"],
                item["license"],
                item["domain"],
                item["scope"],
                item.get("originalFileType"),
                (((self.CurrentPage - 1) * 8) + I)
            ))

            icon_path = os.path.join(temp_dir, item["modelId"])
            if not os.path.exists(icon_path):
                os.makedirs(icon_path)
            thumbnailPath = thumbnail.replace("%2F", "/").replace("?", "/")
            icon_path = os.path.join(icon_path, thumbnailPath.split('/')[-1])
            if not os.path.exists(icon_path):
                try:
                    print(f'Fetching {thumbnail}')
                    filePath = urllib.request.urlretrieve(thumbnail, icon_path)
                    icon_path = os.path.join(item["modelId"], filePath[0])
                except Exception as e:
                    print(e)
                    filePath = Path(__file__ + "\icons\placeholder.png")
                    icon_path = os.path.join(item["modelId"], filePath)

            try:
                thumb = self.pcoll.load(item["modelId"], icon_path, 'IMAGE')
            except:
                thumb = self.pcoll.load(
                    item["modelId"]+str(I), icon_path, 'IMAGE')

            self.partList.append(self.PartStruct(item["modelId"], item["modelFileName"], item.get(
                "originalFileType"), thumb.icon_id, item["domain"], 0))

            if len(item["parts"]) > 0:
                parts = item["parts"]
                X = 1
                for part in parts:
                    print("Getting Thumbnail for {0}".format(part["modelId"]))
                    self.partList.append(self.PartStruct(
                        part["modelId"], part["modelFileName"], part.get("originalFileType"), "", part["domain"], X))

                    thumb_thread = threading.Thread(target=self.get_lazy_thumbs, args=(
                        I, X, part["thumbnailUrl"], part["modelId"], temp_dir)).start()

                    X += 1

            title = item.get('modelTitle') or item.get('modelFileName')
            self.modelList.append(self.ModelStruct(
                modelTitle=title, partList=self.partList[:]))

            I += 1

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
        self.selectionSearching = False
        self.newSearch = False
        self.selectionThumbnailGrab = False

        self.thangs_ui_mode = 'VIEW'

        if self.search_callback is not None:
            self.search_callback()

        print("Search Completed!")

    def get_stl_search(self, stl_path):
        try:
            self.searchType = "Object"
            self.thangs_ui_mode = 'SEARCH'
            self.selectionSearching = True
            self.selectionEmpty = False
            self.stl_callback()

            print("Started STL Search")

            self.CurrentPage = self.PageNumber

            self.pcoll = self.preview_collections["main"]

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

            headers = {
                "Authorization": "Bearer "+self.bearer,
            }

            try:
                isDevOrStaging = 'true' if any([x in os.path.basename(self.Thangs_Config.config_path) for x in ["dev_", "staging_"]]) else 'false'
                url_endpoint = str(
                    self.Thangs_Config.thangs_config['url'])+"api/search/v1/mesh-url?filename=mesh.stl&sendContentLengthRangeHeader="+isDevOrStaging                print(url_endpoint)
                response = requests.get(url_endpoint, headers=headers)
                responseData = response.json()

                # print(responseData)
                signedUrl = responseData["signedUrl"]
                new_Filename = responseData["newFileName"]
            except:
                print("URL BROKEN" + url_endpoint)
                self.selectionSearching = False
                self.searching = False
                self.newSearch = False
                self.selectionFailed = True
                return

            data = open(stl_path, 'rb').read()

            try:
                if isDevOrStaging == 'true':
                    putHeaders = {
                        "Content-Type": "model/stl",
                        "X-Goog-Content-Length-Range": "1,250000000"
                    }
                else:
                    putHeaders = {
                        "Content-Type": "model/stl",
                    }
                putRequest = requests.put(
                    url=signedUrl, data=data, headers=putHeaders)
                print(putRequest.status_code)

                #response = s.post(url, headers=headers, data=data)
            except:
                print("API Failed")
                self.selectionSearching = False
                self.searching = False
                self.newSearch = False
                self.selectionFailed = True
                return

            print("Select Search Returned")

            try:
                url = str(
                    self.Thangs_Config.thangs_config['url']+"api/search/v1/mesh-search?filepath=" + new_Filename)
                print(url)

                response = requests.get(url=url, headers=headers)

                responseData = response.json()
                responseData["searchMetadata"] = {}
                self.display_stl_results(responseData, show_summary=True)
            except Exception as e:
                print("Get Results Broke: ", e)
                self.selectionSearching = False
                self.searching = False
                self.newSearch = False
                self.selectionFailed = True
                return
        except Exception as e:
            print(e)
            self.selectionSearching = False
            self.searching = False
            self.newSearch = False
            self.selectionFailed = True
            return None
