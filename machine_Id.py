import platform

class MachineID():

    def getID(self):
        system = platform.system().lower()

        if "darwin" in system:
            return self.getDarwinMachineId()            
        if "linux" in system:
            return self.getLinuxMachineId()
        if "windows" in system:
            return self.getWindowsMachineId()

        return self.getBSDMachineId()

    def getDarwinMachineId(self):
        try :
            import subprocess
            process = subprocess.Popen(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if stderr != 0:
                print(stderr)
                return ""
            
            for line in stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    parts = line.split(" = ")
                    if len(parts) == 2:
                        return parts[1].strip()
            
            return ""
        except Exception as e:
            print(e)
            return ""

    def getLinuxMachineId(self):
        try:
            f = open("/var/lib/dbus/machine-id", "r")
            idArray = f.readlines()
            return idArray[0].strip()
        except: 
            try :
                f = open("/etc/machine-id", "r")
                idArray = f.readlines()
                return idArray[0].strip()
            except Exception as e:
                print(e)
                return ""
        
    def getWindowsMachineId(self):
        try:
            import winreg
            access_registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            access_key = winreg.OpenKey(access_registry, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY)
            return winreg.QueryValueEx(access_key, "MachineGuid")[0]
        except Exception as e: 
            print(e)
            return ""
    
    def getBSDMachineId(self): 
        try:
            f = open("/etc/hostid", "r")
            idArray = f.readlines()
            return idArray[0].strip()
        except:
            try :
                import subprocess
                process = subprocess.Popen(["kenv", "-q", "smbios.system.uuid"],
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                if stderr != 0:
                    print(stderr)
                    return ""
                return stdout
            except Exception as e:
                print(e)
                return ""