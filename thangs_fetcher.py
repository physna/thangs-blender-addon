import threading
import configparser
import json
import base64
import requests
import uuid
from urllib.request import urlopen
import urllib.request
import urllib.parse
import threading
import os
import math
import platform
from requests.exceptions import Timeout
from .fp_val import FP
from .thangs_events import ThangsEvents
from .config import get_config, ThangsConfig
import bpy
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

        self.modelInfo = []
        self.enumItems = []
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
    
        self.length = []
        self.thumbnailNumbers = []

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

        self.Thangs_Config = ThangsConfig()
        self.amplitude = ThangsEvents()
        self.amplitude.deviceId = socket.gethostname().split(".")[0]
        self.amplitude.deviceOs = platform.system()
        self.amplitude.deviceVer = platform.release()
        self.FP = FP()

        pass

    def reset(self):
        self.search_thread = None
        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""
        self.uuid = ""

        self.modelInfo = []
        self.enumItems = []
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
    
        self.length = []
        self.thumbnailNumbers = []

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

    def cancel(self):
        if self.search_thread is not None:
            self.search_thread.terminate()
            self.search_thread = None
            self.searching = False
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

    def get_http_search(self):
        global thangs_config
        print("Started Search")
        self.searching = True

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

        self.modelInfo.clear()

        self.enumItems.clear()
        self.enumModels1.clear()
        self.enumModels2.clear()
        self.enumModels3.clear()
        self.enumModels4.clear()
        self.enumModels5.clear()
        self.enumModels6.clear()
        self.enumModels7.clear()
        self.enumModels8.clear()
        self.enumModelInfo.clear()
        self.enumModelTotal.clear()
        
        self.length.clear()
        self.thumbnailNumbers.clear()

        self.Directory = self.query
        # Added
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
        self.pcoll.ModelView1 = ()
        self.pcoll.ModelView2 = ()
        self.pcoll.ModelView3 = ()
        self.pcoll.ModelView4 = ()
        self.pcoll.ModelView5 = ()
        self.pcoll.ModelView6 = ()
        self.pcoll.ModelView7 = ()
        self.pcoll.ModelView8 = ()
        self.pcoll.Model_page = self.CurrentPage

        self.preview_collections["main"] = self.pcoll

        self.pcoll = self.preview_collections["main"]

        if self.newSearch == True:
            response = requests.get(self.Thangs_Config.thangs_config['url']+"api/models/v2/search-by-text?page="+str(self.CurrentPage-1)+"&searchTerm="+self.query +
                                    "&pageSize=8&narrow=false&collapse=true&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs",
                                    headers={"x-fp-val": self.FP.getVal(self.Thangs_Config.thangs_config['url']+"fp_m")})
        else:
            response = requests.get(
                str(self.Thangs_Config.thangs_config['url'])+"api/models/v2/search-by-text?page=" +
                str(self.CurrentPage-1)+"&searchTerm="+self.query +
                "&pageSize=8&narrow=false&collapse=true&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs",
                headers={"x-thangs-searchmetadata": base64.b64encode(
                    json.dumps(self.searchMetaData).encode()).decode(),
                    "x-fp-val": self.FP.getVal(self.Thangs_Config.thangs_config['url']+"fp_m")},
            )

        if response.status_code != 200:
            self.amplitude.send_amplitude_event("Text Search - Failed", event_properties={
                'searchTerm': self.query,
            })

        else:
            responseData = response.json()
            items = responseData["results"]  # Each model result is X
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

            self.i = 0
            #self.enumModelTotal.append(("NONE", "None", "", 1))

            for item in items:
                self.enumModelInfo.clear()

                if len(item["thumbnails"]) > 0:
                    thumbnail = item["thumbnails"][0]
                else:
                    thumbnailAPIURL = item["thumbnailUrl"]
                    thumbnailURL = requests.head(thumbnailAPIURL)
                    thumbnail = thumbnailURL.headers["Location"]

                modelTitle = item["modelTitle"]
                modelId = item["modelId"]        

                # Stateful Model Information
                self.modelInfo.append(
                    tuple([modelTitle, item["attributionUrl"], modelId, (((self.CurrentPage-1)*8) + self.i), self.i, item["domain"], item["scope"]]))
                self.enumItems.append(
                    (modelTitle, modelId, item["ownerUsername"], item["license"], item["originalFileType"]))

                thumbnail = thumbnail.replace("https", "http", 1)

                filePath = urllib.request.urlretrieve(thumbnail)

                filepath = os.path.join(modelId, filePath[0])

                thumb = self.pcoll.load(modelId, filepath, 'IMAGE')

                self.thumbnailNumbers.append(thumb.icon_id)

                z = 0

                self.enumModelInfo.append(
                        (modelId, modelTitle, ""))#, z))

                if self.i == 0:
                    self.enumModels1.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 1:
                    self.enumModels2.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 2:
                    self.enumModels3.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 3:
                    self.enumModels4.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 4:
                    self.enumModels5.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 5:
                    self.enumModels6.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                elif self.i == 6:
                    self.enumModels7.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                else:
                    self.enumModels8.append(
                        (modelId, modelTitle, "", thumb.icon_id, z))

                if len(item["parts"]) > 0:
                    parts = item["parts"]
                    self.x = z
                    for part in parts:
                        ModelTitle = part["modelFileName"]
                        modelID = part["modelId"]
                        thumbnailAPIURL = part["thumbnailUrl"]
                        try:
                            thumbnailURL = requests.head(
                                thumbnailAPIURL, timeout=5)
                        except Timeout:
                            continue
                        thumbnail = thumbnailURL.headers["Location"]
                        thumbnail = thumbnail.replace("https", "http", 1)
                        filePath = urllib.request.urlretrieve(thumbnail)
                        filepath = os.path.join(modelID, filePath[0])
                        thumb = self.pcoll.load(modelID, filepath, 'IMAGE')

                        self.enumModelInfo.append(
                            (modelID, ModelTitle, ""))#, self.x+1))

                        if self.i == 0:
                            self.enumModels1.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 1:
                            self.enumModels2.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 2:
                            self.enumModels3.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 3:
                            self.enumModels4.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 4:
                            self.enumModels5.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 5:
                            self.enumModels6.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        elif self.i == 6:
                            self.enumModels7.append(
                                (modelID, ModelTitle, "", thumb.icon_id, self.x+1))

                        else:
                            self.enumModels8.append(
                                (modelId, ModelTitle, "", thumb.icon_id, self.x+1))

                        self.x = self.x + 1

                self.enumModelTotal.append(self.enumModelInfo[:])
                self.i = self.i + 1

        if self.enumModels1:
            self.length.append(len(self.enumModels1))
            self.result1 = self.enumModels1[0][3]
        if self.enumModels2:
            self.length.append(len(self.enumModels2))
            self.result2 = self.enumModels2[0][3]
        if self.enumModels3:
            self.length.append(len(self.enumModels3))
            self.result3 = self.enumModels3[0][3]
        if self.enumModels4:
            self.length.append(len(self.enumModels4))
            self.result4 = self.enumModels4[0][3]
        if self.enumModels5:
            self.length.append(len(self.enumModels5))
            self.result5 = self.enumModels5[0][3]
        if self.enumModels6:
            self.length.append(len(self.enumModels6))
            self.result6 = self.enumModels6[0][3]
        if self.enumModels7:
            self.length.append(len(self.enumModels7))
            self.result7 = self.enumModels7[0][3]
        if self.enumModels8:
            self.length.append(len(self.enumModels8))
            self.result8 = self.enumModels8[0][3]

        self.pcoll.Model = self.enumItems
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

        self.searching = False
        self.newSearch = False

        self.thangs_ui_mode = 'VIEW'

        print("Callback")
        if self.search_callback is not None:
            self.search_callback()

        print("Search Completed!")

        return
