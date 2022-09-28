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
from requests.exceptions import Timeout
from .thangs_events import ThangsEvents
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
import socket

amplitude = ThangsEvents()
amplitude.deviceId = socket.gethostname().split(".")[0]

config_obj = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'prod_config.ini')
config_obj.read(config_path)
thangs_config = config_obj['thangs']

class ThangsFetcher():
    def __init__(self, callback=None):
        self.search_thread = None
        self.search_callback = callback
        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""
        self.devideOS = ""
        self.deviceVer = ""
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
        self.licenses = []
        self.creators = []
        self.filetype = []
        self.length = []
        self.thumbnailNumbers = []

        self.preview_collections = {}
        self.searchMetaData = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1

        self.searching = False
        self.failed = False
        self.newSearch = False
        pass

    def reset(self):
        self.search_thread = None
        self.context = ""
        self.thangs_ui_mode = ''
        self.Directory = ""
        self.pcoll = ""
        self.query = ""

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
        self.licenses = []
        self.creators = []
        self.filetype = []
        self.length = []
        self.thumbnailNumbers = []

        self.preview_collections = {}

        self.totalModels = 0
        self.PageTotal = 0
        self.PageNumber = 1
        self.CurrentPage = 1

        self.searching = False
        self.failed = False

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
                amplitude.send_amplitude_event("Text Search - No Results", event_properties={
                    'searchTerm': items['originalQuery'],
                    'searchId': self.uuid,
                    'numOfMatches': items['totalResults'],
                    'pageCount': items['page'],
                    'searchMetadata': self.searchMetaData,
                    'source': "blender",
                })
            else:
                amplitude.send_amplitude_event("Text Search - Results", event_properties={
                    'searchTerm': items['originalQuery'],
                    'searchId': self.uuid,
                    'numOfMatches': items['totalResults'],
                    'pageCount': items['page'],
                    'searchMetadata': self.searchMetaData,
                    'source': "blender",
                })

    def get_http_search(self):
        global thangs_config
        print("Started Search")
        self.searching = True

        self.Directory = self.query
        # Added
        self.CurrentPage = self.PageNumber

        amplitude.send_amplitude_event("Text Search Started", event_properties={
            'searchTerm': self.query,
            'source': "blender",
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

        self.licenses.clear()
        self.creators.clear()
        self.filetype.clear()
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
            response = requests.get(thangs_config['url']+"api/models/v2/search-by-text?page="+str(self.CurrentPage-1)+"&searchTerm="+self.query +
                                    "&pageSize=8&narrow=false&collapse=true&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs")
        else:
            response = requests.get(
                str(thangs_config['url'])+"api/models/v2/search-by-text?page=" +
                str(self.CurrentPage-1)+"&searchTerm="+self.query +
                "&pageSize=8&narrow=false&collapse=true&fileTypes=stl%2Cgltf%2Cobj%2Cfbx%2Cglb%2Csldprt%2Cstep%2Cmtl%2Cdxf%2Cstp&scope=thangs",
                headers={"x-thangs-searchmetadata": base64.b64encode(
                    json.dumps(self.searchMetaData).encode()).decode()},
            )

        if response.status_code != 200:
            amplitude.send_amplitude_event("Search Failed", event_properties={
                'device_os': str(self.devideOS),
                'device_ver': str(self.deviceVer),
                'searchTerm': self.query,
                'source': "blender"
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

                amplitude.send_thangs_event("Capture", data)

            self.get_total_results(response)

            self.i = 0
            for item in items:
                if len(item["thumbnails"]) > 0:
                    thumbnail = item["thumbnails"][0]
                else:
                    thumbnailAPIURL = item["thumbnailUrl"]
                    thumbnailURL = requests.head(thumbnailAPIURL)
                    thumbnail = thumbnailURL.headers["Location"]

                modelTitle = item["modelTitle"]
                product_url = item["attributionUrl"]
                modelId = item["modelId"]
                searchIndex = ((self.CurrentPage-1)*8) + self.i
                position = self.i
                domain = item["domain"]
                scope = item["scope"]

                # Stateful Model Information
                self.modelInfo.append(
                    tuple([modelTitle, product_url, modelId, searchIndex, position, domain, scope]))
                self.enumItems.append(
                    (modelTitle, modelId, item["ownerUsername"], "LCs Coming Soon!", item["originalFileType"]))

                thumbnail = thumbnail.replace("https", "http", 1)

                filePath = urllib.request.urlretrieve(thumbnail)

                filepath = os.path.join(modelId, filePath[0])

                thumb = self.pcoll.load(modelId, filepath, 'IMAGE')

                self.thumbnailNumbers.append(thumb.icon_id)

                z = 0
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
                        filePath = filePath[0]
                        filepath = os.path.join(modelID, filePath)
                        thumb = self.pcoll.load(modelID, filepath, 'IMAGE')
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
                self.i = self.i + 1

        if self.enumModels1:
            self.length.append(len(self.enumModels1))
        if self.enumModels2:
            self.length.append(len(self.enumModels2))
        if self.enumModels3:
            self.length.append(len(self.enumModels3))
        if self.enumModels4:
            self.length.append(len(self.enumModels4))
        if self.enumModels5:
            self.length.append(len(self.enumModels5))
        if self.enumModels6:
            self.length.append(len(self.enumModels6))
        if self.enumModels7:
            self.length.append(len(self.enumModels7))
        if self.enumModels8:
            self.length.append(len(self.enumModels8))

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
