class FP:
    val = ""

    def getVal(self, url):

        if FP.val == "":
            import requests
            from .machine_id import MachineID
            
            machineID = MachineID().getID()
            try: 
                response = requests.post(url, json={ 'machineID': machineID })
                FP.val = response.text
                return FP.val
            except:
                return FP.val
    
    