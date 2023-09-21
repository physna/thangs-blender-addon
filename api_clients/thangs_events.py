import requests
import threading
import logging
import socket
import platform
import uuid
import json
import os

from config import get_config

log = logging.getLogger(__name__)

class ThangsEvents(object):
    def __init__(self):
        self.__Thangs_Config = get_config()
        self.__ampURL = self.__Thangs_Config.thangs_config['event_url']
        self.__addon_version = self.__Thangs_Config.version
        self.__cached_deviceId = None
        self.__deviceId = self.get_deviceId()
        self.__deviceOs = platform.system()
        self.__deviceVer = platform.release()
        pass

    def send_thangs_event(self, event_type, event_properties=None):
        threading.Thread(
            target=self._send_thangs_event,
            args=(event_type, event_properties)
        ).start()
        return

    def _send_thangs_event(self, event_type, event_properties):
        if event_type == "Results":
            requests.post(self.__Thangs_Config.thangs_config['url']+"api/search/v1/result",
                          json=event_properties,
                          headers={},
                          )

        elif event_type == "Capture":
            requests.post(self.__Thangs_Config.thangs_config['url']+"api/search/v1/capture-text-search",
                          json=event_properties,
                          headers={
                              "x-device-id": self.__deviceId},
                          )

    def send_amplitude_event(self, event_name, event_properties=None):
        print('seinding event device ID:',str(self.__deviceId))
        if event_name != "Thangs Blender Addon - Heartbeat" and event_name != "Thangs Blender Addon - Opened":
            print(f"Running {event_name}")
        threading.Thread(
            target=self._send_amplitude_event,
            args=(event_name, event_properties)
        ).start()
        return

    def _construct_event(self, event_name, event_properties):
        event = {
            'event_type': event_name,
            'device_id': str(self.__deviceId),
            'event_properties': {
                'addon_version': str(self.__addon_version),
                'device_os': str(self.__deviceOs),
                'device_ver': str(self.__deviceVer),
                'source': "blender",
            }
        }
        if event_properties:
            event['event_properties'] |= event_properties
        return event

    def _send_amplitude_event(self, event_name, event_properties):
        event = self._construct_event(event_name, event_properties)
        try:
            response = requests.post(self.__ampURL, json={'events': [event]})
            log.info('Sent amplitude event: ' + event_name + 'Response: ' + str(response.status_code) + " " +
                     response.headers['x-cloud-trace-context'])
        except Exception as e:
            print(e)

    def __get_device_id_json_file_location(self) -> str:
        device_id_location = os.path.join(
            os.path.dirname(get_config().main_addon_file_location), 'deviceId.json')
        return device_id_location

    def get_deviceId(self):
        try:
            if self.__cached_deviceId != None:
                return self.__cached_deviceId
            
            if os.path.exists(self.__get_device_id_json_file_location()):
                deviceId_location = self.__get_device_id_json_file_location()
                deviceId_file = open(deviceId_location)
                data = json.load(deviceId_file)
                self.__cached_deviceId = data["deviceId"]
                return self.__cached_deviceId
            
            self.__cached_deviceId = str(uuid.uuid4())
            deviceId = {
                'deviceId': self.__cached_deviceId,
            }

            with open(self.__get_device_id_json_file_location(), 'w') as json_file:
                json.dump(deviceId, json_file)
            return self.__cached_deviceId
        except Exception as e:
            print(e)
            self.__cached_deviceId = socket.gethostname().split(".")[0]
            return self.__cached_deviceId

__thangs_events__: ThangsEvents = None

def get_thangs_events():
    global __thangs_events__

    if not __thangs_events__:
        __thangs_events__ = ThangsEvents()

    return __thangs_events__

