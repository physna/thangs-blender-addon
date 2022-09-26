import threading
import requests
import threading
import time


class ThangsEvents(object):
    def __init__(self):
        self.deviceId = ""
        self.ampURL = 'https://production-api.thangs.com/system/events'
        pass

    def send_thangs_event(self, event_type, event_properties=None):
        threading.Thread(
            target=self._send_thangs_event,
            args=(event_type, event_properties)
        ).start()
        return

    def _send_thangs_event(self, event_type, event_properties):
        if event_type == "Results":
            requests.post("https://thangs.com/api/search/v1/result",
                          json=event_properties,
                          headers={},
                          )

        elif event_type == "Capture":
            requests.post("https://thangs.com/api/search/v1/capture-text-search",
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
            'event_type': self._event_name(event_name),
            'device_id': str(self.deviceId),
            'event_properties': {}
        }
        if event_properties:
            event['event_properties'] = event_properties

        return event

    def _event_name(self, name):
        if name == "Thangs Model Link":
            return
        return "Text Search - " + name

    def _send_amplitude_event(self, event_name, event_properties):
        event = self._construct_event(event_name, event_properties)

        if event_name == "heartbeat":
            while(True):
                requests.post(self.ampURL, json=[event])
                time.sleep(300)
        requests.post(self.ampURL, json=[event])
