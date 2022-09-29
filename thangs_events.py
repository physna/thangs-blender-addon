from itertools import product
import threading
import configparser
import requests
import threading
import time
import logging

from .config import ThangsConfig, get_config

log = logging.getLogger(__name__)

class ThangsEvents(object):
    def __init__(self):
        self.deviceId = ""
        self.Thangs_Config = get_config()
        self.ampURL = self.Thangs_Config.thangs_config['event_url']
        self.addon_version = self.Thangs_Config.version
        self.deviceVer = ""
        self.deviceOs = ""
        pass

    def send_thangs_event(self, event_type, event_properties=None):
        threading.Thread(
            target=self._send_thangs_event,
            args=(event_type, event_properties)
        ).start()
        return

    def _send_thangs_event(self, event_type, event_properties):
        if event_type == "Results":
            requests.post(self.Thangs_Config.thangs_config['url']+"api/search/v1/result",
                          json=event_properties,
                          headers={},
                          )

        elif event_type == "Capture":
            requests.post(self.Thangs_Config.thangs_config['url']+"api/search/v1/capture-text-search",
                          json=event_properties,
                          headers={
                              "x-device-id": self.deviceId},
                          )

    def send_amplitude_event(self, event_name, event_properties=None):
        threading.Thread(
            target=self._send_amplitude_event,
            args=(event_name, event_properties)
        ).start()
        return

    def _construct_event(self, event_name, event_properties):
        event = {
            'event_type': event_name,
            'device_id': str(self.deviceId),
            'event_properties': {
                'addon_version': str(self.addon_version),
                'device_os': str(self.deviceOs),
                'device_ver': str(self.deviceVer),
                'source': "blender",
            }
        }
        if event_properties:
            event['event_properties'] |= event_properties

        return event

    def _send_amplitude_event(self, event_name, event_properties):
        event = self._construct_event(event_name, event_properties)
        response = requests.post(self.ampURL, json={'events': [event]})
        log.info('Sent amplitude event: ' + event_name + 'Response: ' + str(response.status_code) + " " + response.headers['x-cloud-trace-context'])
