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
        self.ampURL = 'https://production-api.thangs.com/system/events'
        pass

    def send_amplitude_event(self, event_name, event_properties=None):
        threading.Thread(
            target=self.amplitudeEventCall, args=(event_name, event_properties)
        ).start()
        return

    def construct_event(self, event_name, event_properties):
        event = {
            "event_type": self.event_name(event_name),
            "device_id": str(self.deviceId),
            "device_os": str(self.devideOS),
            "device_ver": str(self.deviceVer)
        }
        if event_properties:
            event.event_properties = event_properties

        return event

    def event_name(self, name):
        return "thangs breeze - " + name

    def amplitudeEventCall(self, event_name, event_properties):
        event = self.construct_event(event_name, event_properties);
        requests.post(self.ampURL, json=event)