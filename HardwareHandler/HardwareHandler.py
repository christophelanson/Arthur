# Class qui créer chaque hardware à partir de la classe qui lui est associée. Puis lance chaque hardware créé, sans erreur, dans des threads //.
# Chaque hardware est stocké dans un dictionnaire avec le nom du hardware comme clé.
# Chaque hardware doit posseder une fonction get, un paramètre isCommand et un paramètre command afin de pouvoir communiquer avec lui. 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from colorama import Fore


#class HardwareHandlerSignals(QObject):

 #   getSignal = pyqtSignal(str)


class HardwareHandler(QObject):
    
    def __init__(self):
        self.threadPool = QThreadPool()
        #self.signals = HardwareHandlerSignals()
        self.hardwareDict = {}
        self.signalDict = {}
        self.hardwareDictId = {}
        self.dictThread = {}
    
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
            self.hardwareDictId[param[-1]] = hardwareName
            #self.signalDict[hardwareName] = pyqtSignal(str)
            #self.signalDict[hardwareName].connect(self.hardwareDict[hardwareName].get)
            print(f"{Fore.GREEN}INFO (hardwareHandler) -> {hardwareName} launch")
        except Exception as e:
            print(f"{Fore.RED}ERROR (hardwareHandler) -> Error while lauching --{hardwareName}--:")
            print(f"{Fore.RED}    {e}")
        
            
    def runThreadHardware(self):
        print(f"{Fore.GREEN}INFO (hardwareHandler) -> Opening threads for {self.hardwareDict.keys()}")
        for hardware in self.hardwareDict.keys():
            #hardware = self.hardwareDict[hardware]
            self.threadPool.start(self.hardwareDict[hardware])
            #self.dictThread[hardware.hardwareName] = threading.Thread(name=hardware.hardwareName, target=hardware.runPara)
            #self.dictThread[hardware.hardwareName].setDaemon(True)
            #self.dictThread[hardware.hardwareName].start()
            
    # Permet de communiquer avec un hardware se trouvant dans le dictionnaire (en local)
    # Le paramètre command permet de setup la command destiné au hardware
    # Le paramètre isCommand demande au hardware d'executer la commande en // dans la boucle while du hardware, aucun retour attendu 
    # La fonction get return un restult en focntion de la commande. Le système attend la réponse pour continuer.
    #def sendSignal(self, hardwareName, message):

     #   self.signalDict[hardwareName].emit(message)
        # if not isReturn:
        #     hardware.command = command
        #     hardware.isCommand = True
        #     print(f"{Fore.GREEN}INFO (hardwareHandler) -> Send set command '{command}' to {hardware.hardwareName}")
        # else:
        #     getRes = hardware.get(command)
        #     print(f"{Fore.GREEN}INFO (hardwareHandler) -> Send get command '{command}' to {hardware.hardwareName} and got {getRes}")
        #     return getRes  # Execute chaque hardware créé dans un thread //
  
        
        
        