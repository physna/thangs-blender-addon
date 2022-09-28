from itertools import product
import threading
import configparser
import requests
import threading
import time
import logging
import os

# config_file = open(os.path.join(__location__, 'configfile.ini'))

config_obj = configparser.ConfigParser(allow_no_value=True)
config_path = os.path.join(os.path.dirname(__file__), 'prod_config.ini')
config_obj.read(config_path)
thangs_config = config_obj['thangs']

log = logging.getLogger(__name__)


class ThangsEvents(object):
    def __init__(self):
        self.deviceId = ""
        self.ampURL = thangs_config['event_url']
        pass

    def send_thangs_event(self, event_type, event_properties=None):
        threading.Thread(
            target=self._send_thangs_event,
            args=(event_type, event_properties)
        ).start()
        return

    def _send_thangs_event(self, event_type, event_properties):
        if event_type == "Results":
            requests.post(thangs_config['url']+"api/search/v1/result",
                          json=event_properties,
                          headers={},
                          )

        elif event_type == "Capture":
            requests.post(thangs_config['url']+"api/search/v1/capture-text-search",
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
            'event_properties': {}
        }
        if event_properties:
            event['event_properties'] = event_properties

        return event

    def _send_amplitude_event(self, event_name, event_properties):
        event = self._construct_event(event_name, event_properties)
        response = requests.post(self.ampURL, json={'events': [event]})
        log.info('Sent amplitude event: ' + event_name + 'Response: ' + str(response.status_code) + " " + response.headers['x-cloud-trace-context'])
