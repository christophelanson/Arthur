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
#from UI import UI  #Interface graphique
from  Motor import Motor
from Lidar import lidar
from MiniLidar import MiniLIdar
from Camera import Camera
from Gyro import Gyro
from Radio import Radio
from DataBase import DataBase


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        
        with open('Main/idRobot.json') as f: #Permet de recuperer l'uinque ID associé a la carte
            self.idRobot = json.load(f)
        print(f"{Fore.GREEN}INFO (main) -> Initialising {self.idRobot}")
        listSensor = ["gyro", "miniLidar", "motor"] 
        self.dataBase = DataBase.DataBase("main")
        self.dataBase.initSensorTable(listSensor)
        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware, 3 ème paramètre paramètre d'init de la classe

        self.hardwareHandler.addHardware("radio", Radio.Radio)

        self.hardwareHandler.addHardware("motor", Motor.Motor)

        #self.hardwareHandler.addHardware("camera", Camera.Camera)

        #self.hardwareHandler.addHardware("lidar", lidar.Lidar)

        #self.hardwareHandler.addHardware("miniLidar", MiniLIdar.MiniLidar)

        #self.hardwareHandler.addHardware("gyro", Gyro.Compass)

        #self.hardwareHandler.addHardware("ui", UI.UI, hardwareId)

        self.hardwareHandler.runThreadHardware()
        
        self.gyro = Gyro.Compass()

        layout = QVBoxLayout()
	
        b2 = QPushButton("Run Motor")
        b2.pressed.connect(self.runMotor)    

        b3 = QPushButton("Stop Motor")
        b3.pressed.connect(self.stopMotor) 

        b4 = QPushButton("Camera")
        b4.pressed.connect(self.photoCamera)   

        b8 = QPushButton("Radio send")
        b8.pressed.connect(self.sendRadio) 

        b7 = QPushButton("Close Code")
        b7.pressed.connect(self.closeEvent) 

        b9 = QPushButton("Run Lidar")
        b9.pressed.connect(self.runLidar) 

        self.witchRobotLabel = QLabel()
        self.witchRobotLabel.setText("Witch robot ?")
        self.witchRobot = QLineEdit()

        self.speedInput = QLabel()
        self.speedInput.setText('Motor speed:')
        self.motorSpeed = QLineEdit()

        self.timeInput = QLabel()
        self.timeInput.setText('Motor time:')
        self.motorTime = QLineEdit()

        self.directionInput = QLabel()
        self.directionInput.setText('Motor direction:')
        self.motorDirection = QLineEdit()

        self.gyroValue = QLabel()
        self.gyroValue.setText('Gyro value:')

        self.miniLidarValue = QLabel()
        self.miniLidarValue.setText('Mini lidar value:')

        layout.addWidget(b2)
        layout.addWidget(b3)
        layout.addWidget(b7)
        layout.addWidget(b8)
        layout.addWidget(b9)
        layout.addWidget(self.speedInput)
        layout.addWidget(self.motorSpeed)
        layout.addWidget(self.directionInput)
        layout.addWidget(self.motorDirection)
        layout.addWidget(self.timeInput)
        layout.addWidget(self.motorTime)

        layout.addWidget(self.gyroValue)
        layout.addWidget(self.miniLidarValue)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName="main", on_message=self.on_message, listChannel=self.listChannel)

        timer = QTimer(self)
        timer.setInterval(100)
        timer.timeout.connect(self.updateBoard)
        timer.start()
        

    def updateBoard(self):
        gyroValue = str(self.gyro.getSensorValue()).split("-")
        compass = gyroValue[0]
        picth = gyroValue[1]
        roll = gyroValue[2]

        miniLidarValue = str(self.dataBase.getSensorValue("miniLidar"))

        motorValue = self.dataBase.getSensorValue("motor").split("-")
        motorSpeed = str(motorValue[3])
        motorDirection = str(motorValue[1])
        motorTime = str(motorValue[0])

        self.gyroValue.setText(f"Gyro value : \n\tCompass: {compass} Pitch: {picth} Roll: {roll} ")
        self.miniLidarValue.setText(f"MiniLidar value : \n\t Distance : {miniLidarValue}")
        self.motorSpeed.setPlaceholderText(motorSpeed)
        self.motorDirection.setPlaceholderText(motorDirection)
        self.motorTime.setPlaceholderText(motorTime)

    def runLidar(self):
        self.mqtt.sendMessage(message="command/scan", receiver="lidar")

    def closeEvent(self):
        app.quit()
        100/0

    def sendRadio(self):
        self.mqtt.sendMessage(message="send/bonjour", receiver="radio", awnserNeeded=False)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "state":
            print("State,", self.mqtt.lastSender, "is", self.mqtt.lastPayload)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        
    def runMotor(self):
        payload = str(self.motorTime.text()) + "-" + str(self.motorDirection.text()) + "-0-" + str(self.motorSpeed.text()) + "-0"
        self.dataBase.updateSensorValue("motor", payload)
        payload = "run-" + str(self.motorTime.text()) + "-" + str(self.motorDirection.text()) + "-0-" + str(self.motorSpeed.text()) + "-0"
        if self.witchRobot.text == self.idRobot:
            self.mqtt.sendMessage(message="command/"+payload, receiver="motor")
        else:
            payload = 'motor_'+ 'command/'+  payload
            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")
    
    def stopMotor(self):
        self.mqtt.sendMessage(message="command/stop", receiver="motor")
    
    def photoCamera(self):
        self.mqtt.sendMessage(message="command/capture", receiver="camera")


if __name__ == "__main__":

    app = QApplication([])
    windows = Main()
    sys.exit(app.exec_())
