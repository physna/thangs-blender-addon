from . import addon_updater_ops
import requests
import uuid

class FP:
    def getVal(self, url):
        try:
            settings = addon_updater_ops.get_user_preferences()
            if not settings:
                return ""

            if settings.fp_val == "":
                # Acquire identifier for API requests metrics. 
                response = requests.post(url, json={ 'machineID': str(uuid.uuid4()) })
                json = response.json()
                settings.fp_val = json["fp_val"]
                    
            # Return identifier for request correlation
            return settings.fp_val
        except Exception as e:
            return ""

        

