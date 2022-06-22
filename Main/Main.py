import sys
from sys import *
import json
from colorama import Fore  #Permet de print en couleur
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import time
import numpy as np

sys.path.append(".")
from Mqtt import Mqtt
from HardwareHandler import HardwareHandler #Permet de creer un hardware et d'executer son code en //, les hardwares fonctionnelles sont stockés dans un dictionnaire
from Motor import Motor
from Lidar import Lidar
from MiniLidar import MiniLidar
from Camera import Camera
from Gyro import Gyro
from Radio import Radio
from Wifi import Wifi
from DataBase import DataBase
from RoboticArm import RoboticArm
from Utils import Utils

# from Json import Json
import json



class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
#        self.jsonHandler = Json.JsonHandler()
#        self.idRobot = self.jsonHandler.read("robotID.json")["ID"]
#        self.hardwareList = self.idRobot["hardwareList"]
        # read json robot ID file
        with open('robotID.json') as jsonFile:
            self.robotID = json.load(jsonFile)
        self.hardwareList = self.robotID['ID']['hardwareList']

        print(f"{Fore.GREEN}INFO (main) -> Initialising {self.robotID['ID']['name']}")
        listSensor = ["gyro", "miniLidar", "motor"] 
        self.dataBase = DataBase.DataBase("main")
        self.dataBase.initSensorTable(listSensor)
        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware

        if "wifi" in self.hardwareList:
            self.hardwareHandler.addHardware("wifi", Wifi.Wifi)
        if "radio" in self.hardwareList:
            self.hardwareHandler.addHardware("radio", Radio.Radio)
        if "motor" in self.hardwareList:
            self.hardwareHandler.addHardware("motor", Motor.Motor)
        if "roboticArm" in self.hardwareList:
            self.hardwareHandler.addHardware("roboticArm", RoboticArm.RoboticArm)
        if "camera" in self.hardwareList:
            self.hardwareHandler.addHardware("camera", Camera.Camera)
        #self.hardwareHandler.addHardware("lidar", lidar.Lidar)
        if "miniLidar" in self.hardwareList:
            self.hardwareHandler.addHardware("miniLidar", MiniLidar.MiniLidar)

        #if "gyro" in self.hardwareList:
        #    self.hardwareHandler.addHardware("gyro", Gyro.Compass)

        self.hardwareHandler.runThreadHardware()
        
        if "gyro" in self.hardwareList:
            self.gyro = Gyro.Compass()
### tread minilidar au dessus ?
        if "miniLidar" in self.hardwareList:
            self.miniLidar = MiniLidar.MiniLidar()

        if "lidar" in self.hardwareList:
            self.lidar = Lidar.Lidar()

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName="main", on_message=self.on_message, listChannel=self.listChannel)

        self.showWindow()

        timer = QTimer(self)
        timer.setInterval(500)
        timer.timeout.connect(self.updateBoard)
        timer.start()


    def showWindow(self):
        
        # Robot name
        self.robotNumberLabel = QLabel("Robot name")
        self.robotNumber = QLineEdit(self.robotID['ID']['name'])

        # Motors
        self.motorPayload = QLineEdit("0.8,1,0,50,0")
        self.runMotorButton = QPushButton("Motor run                    ")
        self.runMotorButton.pressed.connect(self.runMotor)    

        self.rotationPayload = QLineEdit("30,1.0,1,0,60,0")
        self.rotationButton = QPushButton("Motor rotate                 ")
        self.rotationButton.pressed.connect(self.motorRotate) 

        self.stopMotorButton = QPushButton("Motor stop")
        self.stopMotorButton.pressed.connect(self.stopMotor) 

        #Camera
        self.cameraButton = QPushButton("Camera")
        self.cameraButton.pressed.connect(self.photoCamera)   

        self.objectsCameraButton = QPushButton("Lidar Objects Camera Shoot")
        self.objectsCameraButton.pressed.connect(self.objectsCamera)

        # Radio and wifi messages
        self.radioSendButton = QPushButton("Send via radio                  ")
        self.radioSendButton.pressed.connect(self.sendRadio) 

        self.wifiSendButton = QPushButton("Send via wifi                    ")
        self.wifiSendButton.pressed.connect(self.sendWifi)

        self.messageRecipient = QLineEdit('recipient name')
        self.messagePayload = QLineEdit("motor/run/3,1,0,30,0")

        # Lidar
        self.runLidarButton = QPushButton("Run Lidar")
        self.runLidarButton.pressed.connect(self.runLidar) 
        
        # Robotic arm
        self.moveRoboticArmButton = QPushButton("Move robotic arm           ")
        self.moveRoboticArmButton.pressed.connect(self.moveRoboticArm) 

        self.foldRoboticArmButton = QPushButton("Fold robotic arm           ")
        self.foldRoboticArmButton.pressed.connect(self.foldRoboticArm) 

        self.roboticArmLabel = QLabel('Robotic arm payload')
        self.roboticArmPayload = QLineEdit("90,200,200,0,90,40")

        # Sequences of actions
        self.fullSequenceButton = QPushButton("Run full sequences   ")
        self.fullSequenceButton.pressed.connect(self.fullSequence)

        self.fullSequenceLabel = QLabel()
        self.fullSequenceLabel.setText("Nb of motor/lidar/camera sequences")
        self.sequencePayload = QLineEdit("1,Left,0,0,AH422,200,80")

        # Close code
        self.closeCodeButton = QPushButton("Close Code")
        self.closeCodeButton.pressed.connect(self.closeEvent) 

        # Informations
        self.gyroValue = QLabel()
        self.gyroValue.setText('Gyro value:')

        self.miniLidarValue = QLabel()
        self.miniLidarValue.setText('Mini lidar value:')

        # Window layout creation
        layout = QFormLayout()
        
        layout.addRow(self.robotNumberLabel,self.robotNumber)
        layout.addRow(QLabel('Motors ------------- distance (m) or angle, radius (degrees, m) then direction, init, max and final speed (%)'))
        layout.addRow(self.runMotorButton,self.motorPayload)
        layout.addRow(self.rotationButton,self.rotationPayload)
        layout.addRow(self.stopMotorButton)
        layout.addRow(QLabel('Camera -------------'))
        layout.addRow(self.cameraButton)
        layout.addRow(self.objectsCameraButton)
        layout.addRow(QLabel('Messages ----------- payload: hardware/instruction/payload'))
        layout.addRow(self.radioSendButton,self.messageRecipient)
        layout.addRow(self.wifiSendButton,self.messagePayload)
        layout.addRow(QLabel('Lidar --------------'))
        layout.addRow(self.runLidarButton)
        layout.addRow(QLabel('Robotic arm --------'))
        layout.addRow(self.moveRoboticArmButton,self.roboticArmPayload)
        layout.addRow(self.foldRoboticArmButton,QLabel('direction, X, Y, incidence, wrist rotation, clamp'))
        layout.addRow(QLabel('Full sequence: nbOfSequences, surveying (Left/Right), X0, Y0, plotName, vineWidth, vineDistance'))
        layout.addRow(self.fullSequenceButton,self.sequencePayload)
        layout.addRow(QLabel('--------------------'))
        layout.addRow(self.closeCodeButton)
        layout.addRow(QLabel('--------------------'))
        layout.addRow(self.gyroValue)
        layout.addRow(self.miniLidarValue)

        w = QWidget()
        w.setLayout(layout)
        self.setWindowTitle("User Interface")
        self.setCentralWidget(w)
        self.show()


    def updateBoard(self):
        
        if "gyro" in self.hardwareList:
            gyroValue = str(self.gyro.getSensorValue()).split(",")
            compass = gyroValue[0]
            picth = gyroValue[1]
            roll = gyroValue[2]
            self.gyroValue.setText(f"Gyro value: \tCompass: {compass} \tPitch: {picth} \tRoll: {roll} ")


    def runLidar(self):
        print("Running Lidar")
        print("Folding Arm")
        payload="90,320,-50,-30,90,40"

        res = bool(self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm", awnserNeeded=True))
        if res: 
            print(f"{Fore.GREEN}INFO (Main) -> robticArm executed {payload} with succes")
        else:
            print(f"{Fore.RED}ERROR (Main) -> robticArm executed {payload} with error")

        print("Collecting Lidar data")

        res = bool(self.mqtt.sendMessage(message="command/scan", receiver="lidar", awnserNeeded=True))
        if res: 
            print(f"{Fore.GREEN}INFO (Main) -> lidar executed with succes")
        else:
            print(f"{Fore.RED}ERROR (Main) -> lidar executed  with error")

        print("Unfolding Arm")
        payload="90,180,250,10,90,40"
        res = bool(self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm", awnserNeeded=True))
        if res: 
            print(f"{Fore.GREEN}INFO (Main) -> robticArm executed {payload} with succes")
        else:
            print(f"{Fore.RED}ERROR (Main) -> robticArm executed {payload} with error")

    def closeEvent(self):
        app.quit()
        100/0

    def sendRadio(self,payload=""):
        if payload == "":
            payload = str(self.messagePayload.text())
        self.mqtt.sendMessage(message=payload, receiver="radio", awnserNeeded=False)

    def sendWifi(self,payload=""):
        if payload == "":
            payload = str(self.messagePayload.text())
        self.mqtt.sendMessage(message=payload, receiver="wifi", awnserNeeded=False)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "state":
            #print("State,", self.mqtt.lastSender, "is", self.mqtt.lastPayload)
            if self.mqtt.lastSender == "miniLidar":
                self.miniLidarValue.setText(f"MiniLidar value: \tDistance : {round(float(self.mqtt.lastPayload))} mm")
        
    def runMotor(self,payload=""):
        if payload == "":
            payload = "run/" + str(self.motorPayload.text())
#        self.dataBase.updateSensorValue("motor", payload)
        payload = "run/" + payload
#        if self.robotNumber.text() == str(self.idRobot["name"]):
        res = bool(self.mqtt.sendMessage(message=payload, receiver="motor", awnserNeeded=True))
        if res: 
            print(f"{Fore.GREEN}INFO (Main) -> motor executed {payload} with succes")
        else:
            print(f"{Fore.RED}ERROR (Main) -> motor executed {payload} with error")
#        else:
#            payload = 'motor_'+ 'command/'+  payload
#            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")
    
    def motorRotate(self,payload=""):
        if payload == "":
            payload = "rotate/" + str(self.rotationPayload.text())
        payload = "rotate/" + payload
#        if self.robotNumber.text() == str(self.idRobot["name"]):
        res = bool(self.mqtt.sendMessage(message=payload, receiver="motor", awnserNeeded=True))
        if res: 
            print(f"{Fore.GREEN}INFO (Main) -> motor executed {payload} with succes")
        else:
            print(f"{Fore.RED}ERROR (Main) -> motor executed {payload} with error")
#        else:
#            payload = 'motor_'+ 'command/'+  payload
#            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")

    def stopMotor(self):
        self.mqtt.sendMessage(message="command/stop", receiver="motor")

    def moveRoboticArm(self,payload=""):
        if payload == "":
            payload = str(self.roboticArmPayload.text())
        #self.dataBase.updateSensorValue("motor", payload)
        #payload = "run-" + str(self.motorTime.text()) + "" + str(self.motorDirection.text()) + "-0-" + str(self.motorSpeed.text()) + "-0"
#        if self.robotNumber.text() == str(self.idRobot["name"]):
            self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm")
#        else:
#            payload = 'roboticArm_'+ 'command/'+  payload
#            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")

    def foldRoboticArm(self):
        payload="90,100,-40,-80,90,80"
        self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm", awnserNeeded=True)
    
    def photoCamera(self,pictureName='pictureName'):
        self.mqtt.sendMessage(message=f"command/{pictureName}", receiver="camera")
        
    def objectsCamera(self,sequenceName='sequence'):

# ADD CORRECTION to angle and distance to take into account the fact that Lidar and Robotic Arm are 
# done 

        # Lidar angle correction (LidarAC)
        # NB a corrected angle will point according to RoboticArm servo angles
        LidarAC = 280
        #load outputObjectsFile.csv
        path_to_output_objects_file = 'Log/outputObjectsFile.csv'
        lidar_objects = np.loadtxt(path_to_output_objects_file, delimiter=",", dtype=float)
        filtered_lidar_objects = []
        for object_nb in range(len(lidar_objects)):
            angle = (lidar_objects[object_nb][1]+lidar_objects[object_nb][3])/2
            distance = (lidar_objects[object_nb][2]+lidar_objects[object_nb][4])/2
            # keep only objects closer than 2000 mm and angle in [0,180] - RobotArm-wise
            angle = LidarAC - angle
            angle, distance = Utils.lidar_to_roboticArm_conversion(angle, distance)
            if distance <= 2000 and angle > 0 and angle < 180:
                filtered_lidar_objects.append([angle, distance])
        filtered_lidar_objects = np.asarray(filtered_lidar_objects)
        for angle, distance in filtered_lidar_objects:
            print(round(angle), distance)
            payload=f"{angle},200,250,20,90,0"
            self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm")
            pictureName=sequenceName+"_"+str(round(angle))
            self.mqtt.sendMessage(message=f"command/{pictureName}", receiver="camera")
            time.sleep(2)
        payload="90,180,250,10,90,40"
        self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm")

    def fullSequence(self,payload=""):
        if payload == "":
            payload = self.sequencePayload.text() 
        
        payload = payload.split(",")
        # nbOfSequences, surveying (Left/Right), X0, Y0, plotName, vineWidth, vineDistance')
        nbOfSequences = payload[0]
        # update json file (plot name, expected vine width and distance)
        with open('robotID.json','r+') as jsonFile:
            data = json.load(jsonFile)
            if payload(5) != "":
                data['lidar']['lidar_kwargs']['expected_width']=payload[5]
            if payload(6) != "":
                data['lidar']['lidar_kwargs']['expected_distance']=payload[6]
            if payload(6) != "":
                data['lidar']['lidar_kwargs']['plot_name']=payload[4]
            json.dump(data,jsonFile)
        nextTurn = payload[1]
        expected_X = payload[2]
        expected_Y = payload[3]

        for sequenceNumber in range(int(nbOfSequences)):
            # motor
            self.runMotor()
            time.sleep(3)
            # lidar
            self.runLidar()
            # save current file in log
            path_to_output_objects_file = 'Log/outputObjectsFile.csv'
            lidar_objects = np.loadtxt(path_to_output_objects_file, delimiter=",", dtype=float)
            np.savetxt(f'Log/outputObjectsFile{sequenceNumber}.csv', lidar_objects, fmt= '%.2f', delimiter=",")
            # pictures
            self.objectsCamera(sequenceName = f'Sequence{sequenceNumber}')


if __name__ == "__main__":

    app = QApplication([])
    windows = Main()
    sys.exit(app.exec_())