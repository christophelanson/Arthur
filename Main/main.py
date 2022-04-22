import sys
from sys import *
import json
from colorama import Fore  #Permet de print en couleur
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


sys.path.append(".")
from Mqtt import Mqtt
from HardwareHandler import HardwareHandler #Permet de creer un hardware et d'executer son code en //, les hardwares fonctionnelles sont stockés dans un dictionnaire
from UI import UI  #Interface graphique
import Motor
#from Lidar import lidar
from Camera import Camera
from Gyro import Gyro
from Radio import Radio
from DataBase import DataBase


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        
        with open('Main/idRobot.json') as f: #Permet de recuperer l'uinque ID associé a la carte
            idRobot = json.load(f)
        print(f"{Fore.GREEN}INFO (main) -> Initialising {idRobot}")
        listSensor = ["gyro", "miniLidar"] 
        self.dataBase = DataBase.DataBase("main")
        self.dataBase.initSensorTable(listSensor)
        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware, 3 ème paramètre paramètre d'init de la classe

        self.hardwareHandler.addHardware("radio", Radio.Radio)

        #self.hardwareHandler.addHardware("motor", Motor.Motor)

        #self.hardwareHandler.addHardware("camera", Camera.Camera)

        #self.hardwareHandler.addHardware("lidar", Lidar.Lidar, self.hardwareHandler, hardwareId)

        #self.hardwareHandler.addHardware("gyro", Gyro.Compass)

        #self.hardwareHandler.addHardware("ui", UI.UI, hardwareId)

        self.hardwareHandler.runThreadHardware()
        
        layout = QVBoxLayout()

        self.l = QLabel("Start")
        b1 = QPushButton("Get motor state")
        b1.pressed.connect(self.getState)

        b2 = QPushButton("Run")
        b2.pressed.connect(self.runMotor)    

        b3 = QPushButton("Stop")
        b3.pressed.connect(self.stopMotor) 

        b4 = QPushButton("Camera")
        b4.pressed.connect(self.photoCamera)    

        b5 = QPushButton("Test database")
        b5.pressed.connect(self.testDataBase) 

        b6 = QPushButton("update database")
        b6.pressed.connect(self.updateDataBase) 

        b8 = QPushButton("Radio send")
        b8.pressed.connect(self.sendRadio) 

        b7 = QPushButton("Close Code")
        b7.pressed.connect(self.closeEvent) 
     

        layout.addWidget(self.l)
        layout.addWidget(b1)
        layout.addWidget(b2)
        layout.addWidget(b3)
        layout.addWidget(b5)
        layout.addWidget(b6)
        layout.addWidget(b7)
        layout.addWidget(b8)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName="main", on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0

    def closeEvent(self):
        app.quit()
        100/0

    def sendRadio(self):
        self.mqtt.sendMessage(message="send/bonjour", receiver="radio", awnserNeeded=False)

    def testDataBase(self):
        listSensor = ["gyro","miniLidar"]
        self.dataBase.insertSensorValue(listSensor)
        self.dataBase.getSensorValue("gyro")

    def updateDataBase(self):
        self.dataBase.updateSensorValue("gyro",100)
        self.dataBase.getSensorValue("gyro")

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "state":
            print("State,", self.mqtt.lastSender, "is", self.mqtt.lastPayload)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        
    def getState(self):
        result = self.mqtt.sendMessage(message="getState/", receiver="motor", awnserNeeded=True)
        print("state received", result) 
    
    def runMotor(self):
        self.mqtt.sendMessage(message="command/run-10-1-0-30-0", receiver="motor")
    
    def stopMotor(self):
        self.mqtt.sendMessage(message="command/stop", receiver="motor")
    
    def photoCamera(self):
        self.mqtt.sendMessage(message="capture/", receiver="camera")


if __name__ == "__main__":

    app = QApplication([])
    windows = Main()
    sys.exit(app.exec_())
