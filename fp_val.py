class FP:
    val = ""

    def getVal(self, url):

        if FP.val == "":
            import requests
            from machine_Id import MachineID

            machineID = MachineID().getID()
            response = requests.post(url, json={ 'machineID': machineID })
            FP.val = response.text
        
        return FP.val
    