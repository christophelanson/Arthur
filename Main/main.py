import sys
import json
from colorama import Fore  #Permet de print en couleur
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

sys.path.append(".")
from HardwareHandler import HardwareHandler #Permet de creer un hardware et d'executer son code en //, les hardwares fonctionnelles sont stockés dans un dictionnaire
from UI import UI  #Interface graphique
import Motor
from Lidar import Lidar
from Camera import Camera
from Gyro import Gyro
from Communication import RadioRobot
from Message import MessageRouter


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        
        with open('Main/idRobot.json') as f: #Permet de recuperer l'uinque ID associé a la carte
            idRobot = json.load(f)
        print(f"{Fore.GREEN}INFO (main) -> Initialising {idRobot}")
        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        #self.messageRouter = MessageRouter.MessageRouter(node=idRobot["node"], hardwareHandler=self.hardwareHandler)
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware, 3 ème paramètre paramètre d'init de la classe
        hardwareId = 0
        #self.hardwareHandler.addHardware("radio", RadioRobot.RadioRobot, idRobot["node"], self.hardwareHandler, hardwareId)
        #hardwareId += 1
        self.hardwareHandler.addHardware("motor", Motor.Motor, self.hardwareHandler, hardwareId)
        #hardwareId += 1
        #self.hardwareHandler.addHardware("camera", Camera.Camera, self.hardwareHandler, hardwareId)
        #hardwareId += 1
        #self.hardwareHandler.addHardware("lidar", Lidar.Lidar, self.hardwareHandler, hardwareId)
        #hardwareId += 1
        #self.hardwareHandler.addHardware("gyro", Gyro.Compass, self.hardwareHandler, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("ui", UI.UI, self.hardwareHandler, hardwareId)

        #self.messageRouter.updateHardware()

        self.hardwareHandler.runThreadHardware()
        #self.communication.setUI(self.UI)

    #def run(self):
        
     #   self.hardwareHandler.runThreadHardware()
        # lance chaque hardware dans un thread
      #  for thread in self.hardwareHandler.dictThread.keys():
       #     self.hardwareHandler.dictThread[thread].join()
        

if __name__ == "__main__":
    app = QApplication([])
    windows = Main()
    app.exec_()
