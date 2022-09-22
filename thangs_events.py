import threading
import requests
from urllib.request import urlopen
import urllib.request
import urllib.parse
import threading
import os
import math
import time
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


class ThangsEvents():
    def __init__(self):
        self.deviceId = ""
        self.devideOS = ""
        self.deviceVer = ""
        self.event_properties = {}
        self.event_name = ""
        self.event_thread = None
        self.ampURL = 'https://production-api.thangs.com/system/events'
        pass

    def sendAmplitudeEvent(self, event_name, event_properties=None):
        self.event_thread = threading.Thread(
            target=self.amplitudeEventCall, args=(event_name, event_properties)).start()
        return

    def amplitudeEventCall(self, event_name, event_properties):
        from .thangs_fetcher import ThangsFetcher
        fetcher = ThangsFetcher()
        if event_name == "heartbeat":
            print("Sending Heartbeat")
            #starttime = time.time()
            # while True:
            blenderHeartbeat = {
                "events": [
                    {
                        "event_type": "thangs-breeze - addon heartbeat",
                        "device_id": str(self.deviceId),
                        "device_os": str(self.devideOS),
                        "device_ver": str(self.deviceVer)
                    }
                ]
            }
            postResponse = requests.post(self.ampURL, json=blenderHeartbeat)
            #time.sleep(600.0 - ((time.time() - starttime) % 600.0))
            return

        elif event_name == "results":
            print("Sending Results Event")
            blenderSearchResults = {
                "events": [
                    {
                        "event_type": "thangs-breeze - search results",
                        "device_id": str(self.deviceId),
                        "event_properties": {
                            "number_of_results": str(fetcher.totalModels)
                        }
                    }
                ]
            }
            postResponse = requests.post(
                self.ampURL, json=blenderSearchResults)
            return

        elif event_name == "startedSearch":
            print("Sending Search Event")
            blenderSearchStarted = {
                "events": [
                    {
                        "event_type": "thangs-breeze - search started",
                        "device_id": str(self.deviceId),
                        "event_properties": {
                            "searchTerm": str(fetcher.query)
                        }
                    }
                ]
            }
            postResponse = requests.post(
                self.ampURL, json=blenderSearchStarted)
            # Come back and add in what to do if getting something besides a 200 response code
            self.failed = False
            return

        elif event_name == "searchCompleted":
            print("Sending Search Completed Event")
            blenderSearchEnded = {
                "events": [
                    {
                        "event_type": "thangs-breeze - search ended",
                        "device_id": str(self.deviceId)
                    }
                ]
            }
            postResponse = requests.post(self.ampURL, json=blenderSearchEnded)
            return

        elif event_name == "searchFailed":
            print("Sending Search Failed Event")
            blenderSearchFailed = {
                "events": [
                    {
                        "event_type": "thangs-breeze - search failed",
                        "device_id": str(self.deviceId)
                    }
                ]
            }
            postResponse = requests.post(self.ampURL, json=blenderSearchFailed)
            self.failed = True
            return

        elif event_name == "toThangs":
            blenderSearchFailed = {
                "events": [
                    {
                        "event_type": "thangs-breeze - nav to thangs",
                        "device_id": str(self.deviceId)
                    }
                ]
            }
            postResponse = requests.post(self.ampURL, json=blenderSearchFailed)
            return

        return
