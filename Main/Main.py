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
from DataBase import DataBase
from RoboticArm import RoboticArm


class Main(QMainWindow):

    def __init__(self):
        super(Main, self).__init__()
        
        with open('robotID.json') as f: #Permet de recuperer l'uinque ID associé a la carte
            self.idRobot = json.load(f)["ID"]
        print(f"{Fore.GREEN}INFO (main) -> Initialising {self.idRobot}")
        listSensor = ["gyro", "miniLidar", "motor"] 
        self.dataBase = DataBase.DataBase("main")
        self.dataBase.initSensorTable(listSensor)
        # créer chaque hardware
        self.hardwareHandler = HardwareHandler.HardwareHandler()
        # 1er paramètre : nom du hardware, 2 ème paramètre class du hardware

        self.hardwareHandler.addHardware("radio", Radio.Radio)

        self.hardwareHandler.addHardware("motor", Motor.Motor)

        self.hardwareHandler.addHardware("roboticArm", RoboticArm.RoboticArm)

        self.hardwareHandler.addHardware("camera", Camera.Camera)

        #self.hardwareHandler.addHardware("lidar", lidar.Lidar)

        self.hardwareHandler.addHardware("miniLidar", MiniLidar.MiniLidar)

        #self.hardwareHandler.addHardware("gyro", Gyro.Compass)

        self.hardwareHandler.runThreadHardware()
        
        self.gyro = Gyro.Compass()

        self.miniLidar = MiniLidar.MiniLidar()

        self.lidar = Lidar.Lidar()

        

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName="main", on_message=self.on_message, listChannel=self.listChannel)

        self.showWindow()

        timer = QTimer(self)
        timer.setInterval(500)
        timer.timeout.connect(self.updateBoard)
        timer.start()
        
    def showWindow(self):
        
	
        self.runMotorButton = QPushButton("Run Motor")
        self.runMotorButton.pressed.connect(self.runMotor)    

        self.stopMotorButton = QPushButton("Stop Motor")
        self.stopMotorButton.pressed.connect(self.stopMotor) 

        self.cameraButton = QPushButton("Camera")
        self.cameraButton.pressed.connect(self.photoCamera)   

        self.objectsCameraButton = QPushButton("Lidar Objects Camera Shoot")
        self.objectsCameraButton.pressed.connect(self.objectsCamera)

        self.radioSendButton = QPushButton("Radio send")
        self.radioSendButton.pressed.connect(self.sendRadio) 

        self.closeCodeButton = QPushButton("Close Code")
        self.closeCodeButton.pressed.connect(self.closeEvent) 

        self.runLidarButton = QPushButton("Run Lidar")
        self.runLidarButton.pressed.connect(self.runLidar) 

        self.robotNumberLabel = QLabel("Robot name")
        self.robotNumber = QLineEdit(self.idRobot["name"])

        self.motorPayload = QLineEdit("3,1,0,50,0")

        self.rotationPayload = QLineEdit("30")
        self.rotationButton = QPushButton("Rotate")
        self.rotationButton.pressed.connect(self.motorRotate) 
        
        self.radioLabel = QLabel('Radio payload')
        self.radioPayload = QLineEdit("send/motor_command/3,1,0,30,0")
        
        self.roboticArmRun = QPushButton("Move robotic arm")
        self.roboticArmRun.pressed.connect(self.runRoboticArm) 

        self.roboticArmLabel = QLabel('Robotic arm payload')
        self.roboticArmPayload = QLineEdit("90,200,200,0,90,40")

        self.fullSequenceButton = QPushButton("Run full sequences")
        self.fullSequenceButton.pressed.connect(self.fullSequence)

        self.fullSequenceLabel = QLabel()
        self.fullSequenceLabel.setText("Nb of motor/lidar/camera sequences")
        self.nbOfSequences = QLineEdit("1")

        self.gyroValue = QLabel()
        self.gyroValue.setText('Gyro value:')

        self.miniLidarValue = QLabel()
        self.miniLidarValue.setText('Mini lidar value:')

        layout = QFormLayout()

        layout.addRow(self.robotNumberLabel,self.robotNumber)
        layout.addRow(self.runMotorButton,self.motorPayload)
        layout.addRow(self.rotationButton,self.rotationPayload)
        layout.addRow(self.stopMotorButton)
        layout.addRow(self.closeCodeButton)
        layout.addRow(self.cameraButton)
        layout.addRow(self.objectsCameraButton)
        layout.addRow(self.radioSendButton,self.radioPayload)
        layout.addRow(self.runLidarButton)
        layout.addRow(self.roboticArmRun,self.roboticArmPayload)
        layout.addRow(self.fullSequenceButton,self.nbOfSequences)
        layout.addRow(self.gyroValue)
        layout.addRow(self.miniLidarValue)

        w = QWidget()
        w.setLayout(layout)
        self.setWindowTitle("User Interface")

        self.setCentralWidget(w)

        self.show()

    def updateBoard(self):
        
        gyroValue = str(self.gyro.getSensorValue()).split(",")
        compass = gyroValue[0]
        picth = gyroValue[1]
        roll = gyroValue[2]

        # miniLidarValue = str(round(self.miniLidar.getSensorValue()))

        motorValue = self.dataBase.getSensorValue("motor").split(",")
        motorSpeed = str(motorValue[3])
        motorDirection = str(motorValue[1])
        motorTime = str(motorValue[0])

        self.gyroValue.setText(f"Gyro value: \tCompass: {compass} \tPitch: {picth} \tRoll: {roll} ")
        # self.miniLidarValue.setText(f"MiniLidar value : \n\t Distance : {miniLidarValue}")
        #self.motorSpeed.setPlaceholderText(motorSpeed)
        #self.motorDirection.setPlaceholderText(motorDirection)
        #self.motorTime.setPlaceholderText(motorTime)

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

    def sendRadio(self):
        self.mqtt.sendMessage(message="send/bonjour", receiver="radio", awnserNeeded=False)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "state":
            #print("State,", self.mqtt.lastSender, "is", self.mqtt.lastPayload)
            if self.mqtt.lastSender == "miniLidar":
                self.miniLidarValue.setText(f"MiniLidar value: \tDistance : {round(float(self.mqtt.lastPayload))} mm")
        
    def runMotor(self):
        payload = str(self.motorPayload.text())
        self.dataBase.updateSensorValue("motor", payload)
        payload = "run," + str(self.motorTime.text()) + "," + str(self.motorDirection.text()) + ",0," + str(self.motorSpeed.text()) + ",0"
        if self.robotNumber.text() == str(self.idRobot["name"]):
            res = bool(self.mqtt.sendMessage(message="command/"+payload, receiver="motor", awnserNeeded=True))
            if res: 
                print(f"{Fore.GREEN}INFO (Main) -> motor executed {payload} with succes")
            else:
                print(f"{Fore.RED}ERROR (Main) -> motor executed {payload} with error")
        else:
            payload = 'motor_'+ 'command/'+  payload
            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")
    
    def motorRotate(self):
        payload = "rotate," +str(self.rotationPayload.text()) + "," + str(self.motorSpeed.text())

        if self.robotNumber.text() == str(self.idRobot["name"]):
            res = bool(self.mqtt.sendMessage(message="command/"+payload, receiver="motor", awnserNeeded=True))
            if res: 
                print(f"{Fore.GREEN}INFO (Main) -> motor executed {payload} with succes")
            else:
                print(f"{Fore.RED}ERROR (Main) -> motor executed {payload} with error")
        else:
            payload = 'motor_'+ 'command/'+  payload
            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")

    def runRoboticArm(self):
        payload = str(self.roboticArmPayload.text())
        #self.dataBase.updateSensorValue("motor", payload)
        #payload = "run-" + str(self.motorTime.text()) + "" + str(self.motorDirection.text()) + "-0-" + str(self.motorSpeed.text()) + "-0"
        if self.robotNumber.text() == str(self.idRobot["name"]):
            self.mqtt.sendMessage(message="command/"+payload, receiver="roboticArm")
        else:
            payload = 'roboticArm_'+ 'command/'+  payload
            self.mqtt.sendMessage(message="send/"+payload, receiver="radio")

    def stopMotor(self):
        self.mqtt.sendMessage(message="command/stop", receiver="motor")
    
    def photoCamera(self,pictureName='pictureName'):
        self.mqtt.sendMessage(message=f"command/{pictureName}", receiver="camera")
        
    def objectsCamera(self,sequenceName='sequence'):

# ADD CORRECTION to angle and distance to take into account the fact that Lidar and Robotic Arm are distant

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

    def fullSequence(self):
        nbOfSequences = self.nbOfSequences.text() 
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