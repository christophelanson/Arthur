# Class qui créer chaque hardware à partir de la classe qui lui est associée. Puis lance chaque hardware créé, sans erreur, dans des threads //.
# Chaque hardware est stocké dans un dictionnaire avec le nom du hardware comme clé.
# Chaque hardware doit posseder une fonction get, un paramètre isCommand et un paramètre command afin de pouvoir communiquer avec lui. 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from colorama import Fore

class HardwareHandler(QObject):
    
    def __init__(self):
        self.threadPool = QThreadPool()
        self.hardwareDict = {}
        self.signalDict = {}
        self.hardwareDictId = {}
        self.dictThread = {}
        self.countHardware = 0 
    
    # Créer un hardware à partir de du code de class associé
    # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware, 3 ème paramètre paramètre d'init de la classe
    def addHardware(self, hardwareName, hardware, *param):
        try:
            if len(param) != 0:
                if len(param) == 1 :
                    self.hardwareDict[hardwareName] = hardware(param[0])
                if len(param) == 2 :
                    self.hardwareDict[hardwareName] = hardware(param[0], param[1])
                if len(param) == 3 :
                    self.hardwareDict[hardwareName] = hardware(param[0], param[1], param[2])
            else:
                self.hardwareDict[hardwareName] = hardware()
            self.hardwareDictId[self.countHardware] = hardwareName
            self.countHardware += 1 

            print(f"{Fore.GREEN}INFO (hardwareHandler) -> {hardwareName} launch")
        except Exception as e:
            print(f"{Fore.RED}ERROR (hardwareHandler) -> Error while lauching --{hardwareName}--:")
            print(f"{Fore.RED}    {e}")
        
            
    def runThreadHardware(self):
        print(f"{Fore.GREEN}INFO (hardwareHandler) -> Opening threads for {self.hardwareDict.keys()}")
        for hardware in self.hardwareDict.keys():
            self.threadPool.start(self.hardwareDict[hardware])

  
        
        
        