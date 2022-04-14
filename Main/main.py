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
from Lidar import lidar
from Camera import Camera
from Gyro import Gyro
from Communication import RadioRobot
from Mqtt import Mqtt


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        
        with open('Main/idRobot.json') as f: #Permet de recuperer l'uinque ID associé a la carte
            idRobot = json.load(f)
        print(f"{Fore.GREEN}INFO (main) -> Initialising {idRobot}")

        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware, 3 ème paramètre paramètre d'init de la classe
        hardwareId = 0
        self.hardwareHandler.addHardware("radio", RadioRobot.RadioRobot, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("motor", Motor.Motor, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("camera", Camera.Camera, self.hardwareHandler, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("lidar", Lidar.Lidar, self.hardwareHandler, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("gyro", Gyro.Compass, self.hardwareHandler, hardwareId)
        hardwareId += 1
        self.hardwareHandler.addHardware("ui", UI.UI, hardwareId)

        self.hardwareHandler.runThreadHardware()
        
        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b = QPushButton("DANGER!")
        b.pressed.connect(self.getState)

        layout.addWidget(self.l)
        layout.addWidget(b)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName="UI", on_message=self.on_message, listChannel=self.listChannel)


    def on_message(self, client, data, message):
        print("message topic:", message.topic)
        print("client:", client.id)
        print("message", str(message.payload.decode()))
        

    def getState(self):
        self.mqtt.client.publish("all","get state")


if __name__ == "__main__":
    app = QApplication([])
    windows = Main()
    app.exec_()
