class FP:
    val = ""

    def getVal(self, url):

        if FP.val == "":
            import requests
            from .machine_id import MachineID
            
            # Acquire stable identifier for API requests metrics. 
            machineID = MachineID().getID()
            try: 
                # Post identifier to backend for aggregation
                response = requests.post(url, json={ 'machineID': machineID })
                FP.val = response.text
                return FP.val # Return identifier for request correlation
            except:
                return FP.val
    
    