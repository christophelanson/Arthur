import tkinter as tk
from tkinter import ttk
import sys
from HardwareHandler.HardwareHandler import HardwareHandler

from Message.MessageRouter import MessageRouter
sys.path.insert(0, 'Communication')
sys.path.insert(0, 'Motor')
sys.path.insert(0, 'ExceptionFolder')
sys.path.insert(0, 'HardwareHandler')
#import RadioCommunication
import multiprocessing
import Motor
import ExceptionFile
import threading
import ctypes
from colorama import Fore 
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt

        
class fileReader:

    def read(self, name):
        with open(name, "r") as fichier:
            return fichier.read()

    def write(self, name, data):
        with open(name, "w") as fichier:
                    fichier.write(data)
            
    def addContent(self, name, data):
        with open(name, "r") as fichier:
            oldData = fichier.read()
        newData = oldData + newData
        with open(name, "w") as fichier:
            fichier.write(newData)
            

class UI(QRunnable):

    def __init__(self, hardwareHandler:HardwareHandler, hardwareId):
        super(UI, self).__init__()

        self.hardwareName ="ui"
        self.hardwareId = hardwareId
        self.hardwareHandler = hardwareHandler
        self.isMaster = True
        self.id_process = 0
        self.idCommand = False
        self.idReceived = None
        self.oldPayload = []
        self.isListenProcess = False
        self.timeMove = 1
        self.direction = 1
        self.initSpeed = 0
        self.maxSpeed = 30
        self.finalSpeed = 0
        self.maxRotSpeed = 40
        self.numeroDeFichier = 0
        self.logContent = ""
        self.fileReader= fileReader()
        self.pathLogId = self.fileReader.read("Log/pathLogId.txt")
        self.fileReader.write("Log/pathLogId.txt", str(int(self.pathLogId) + 1 ))
        self.pathLog = "Log/log/"+self.pathLogId + ".txt"
        self.functionPara = ""
        self.commandMotor = ""
        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)


    def on_message(self, client, data, message):
        print("message topic:", message.topic)
        print("message", str(message.payload.decode()))
    
    def get(self, command):
        if command == "getState":
            return self.state

    def setThreadId(self, threadCommunicationId, threadmotorId):
        self.threadCommunicationId = threadCommunicationId
        self.threadmotorId = threadmotorId
        print("Thread Id set up")

    @pyqtSlot()  
    def run(self):
        layout = QVBoxLayout()
        b = QPushButton("get Motor State")
        b.pressed.connect(self.getState)
        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)
        self.show()
      
    def getState(self):
        self.mqtt.client.publish("all","motor/get state")

    def sendCommand(self):

        receiver = 2
        hardware = "motor"
        commandType = "straight"
        command = self.createMoveCommand(commandType)
        
        Instruction = self.messageRouter.route(receiver, hardware, command, isSet=True)
        
    
    def createMoveCommand(commandType):
        
        if commandType == "straight":
            command = [dictCommande["RUN"], int(self.timeMove.get()),
                       int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                       int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get())]
            
        if commandType == "turn":
            command = [dictCommande["TURN"], int(self.timeMove.get()),
                   int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                   int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()),
                   int(self.maxRotSpeed.get())]
            
        print(f"{Fore.GREEN}INFO (UI) -> {commandType} command '{command}' created")
        
        return command
    
    def getMotorState(self):
        senderName  = self.messageRouter.node
        receiverName = 2
        hardwareName = "motor"
        command = "getState"
        motorState = self.messageRouter.route(senderName=senderName, receiverName=receiverName, hardwareName=hardwareName, command=command, isReturn=1, channel="radio")
        print(f"{Fore.BLUE}DEBUG (UI) -> motor state {motorState}")

    def runMotorSend(self):
        pass

    def incrementFileNb(self):
        self.logContent == self.numeroDeFichier + self.logContent + "\n"
        self.numeroDeFichier += 1
        self.fileReader.addContent(self.pathLog, self.logContent)
        self.logContent = ""
    
    def cameraPhoto(self):
        self.camera.numeroDeFichier = self.numeroDeFichier
        self.camera.isCapture = True
        
    def cameraSend(self):
        command = [self.rc.dictCommande["PHOTO"]]
        self.send(command)
        self.idCommand = not self.idCommand
    
    def scanLidar(self):
        self.lidar.numeroDeFichier = self.numeroDeFichier
        self.lidar.isScan = True
    
    def scanSend(self):
        command = [self.rc.dictCommande["SCAN"]]
        self.send(command)
        self.idCommand = not self.idCommand
        
#     def runMotorSend(self):
#         #self.incrementFileNb()
#         command = [self.rc.dictCommande["RUN"], int(self.timeMove.get()),
#                    int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
#                    int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()), self.idCommand]
#         print("Commande send:", command)
#         self.commandMotor = command
#         self.send(command)
#         self.idCommand = not self.idCommand
#         

    def turnMotorSend(self):
        #self.incrementFileNb()
        command = [self.rc.dictCommande["TURN"], int(self.timeMove.get()),
                   int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                   int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()),
                   int(self.maxRotSpeed.get()), self.idCommand]
        print("Commande sent:", command)
        self.commandMotor = command
        self.send(command)
        self.idCommand = not self.idCommand

    def stopMotorSend(self):
        command = [self.rc.dictCommande["STOP"], self.idCommand]
        self.send(command)
        self.idCommand = not self.idCommand
        
    def send(self, command):
        self.rc.commandToSend = command
        exception = ExceptionFile.StopListeningSendMessage()
        Null = 0
        found = False
        target_tid = 0
        for tid, tobj in threading._active.items():
            if str(self.threadCommunicationId) == str(tobj):
                found = True
                target_tid = tid
                break
        ret = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), ctypes.py_object(exception))
        if ret == 0:
            print("Invalid thread ID")
        if ret > 1 :
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(target_tid), NULL)
            print("Communication with listen thread failed")
        print("Communication with listen thread succed")
        
    def commandMotorReceived(self, funcDriveMotor, DriveMotorCommand):
        self.motor.func = funcDriveMotor
        self.motor.command = DriveMotorCommand
        self.motor.isCommand = True

    def decodeReiceivedMessage(self,messageReceive):
        payload = []
        for i, data in enumerate(messageReceive):
            payload.append(int(hex(ord(data)), 16))
        if payload[0] != 0 and payload[-1] != 64:
            print("erreur with payload received, first or last char wrong")
        else:
            # evite les redondances de commandes
            if payload == self.oldPayload:
                return
            self.oldPayload = payload

            payload = payload[2:-1]
            action = payload[0]
            print("action", action)
            if action == self.rc.dictCommande["SCAN"]:
                self.logContent += " SCAN"
                self.scanLidar()
                
            if action == self.rc.dictCommande["PHOTO"]:
                self.logContent += " PHOTO"
                self.cameraPhoto()
                
            if action == self.rc.dictCommande["RUN"]:
                self.incrementFileNb()
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                self.logContent += " RUN " + payload
                self.commandMotorReceived("RUN", payload)

            if action == self.rc.dictCommande["TURN"]:
                self.incrementFileNb()
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                print("maxSpeedRot", payload[5])
                self.logContent += " TURN " + payload
                self.commandMotorReceived("TURN", payload)

            if action == self.rc.dictCommande["STOP"]:
                self.commandMotorReceived("STOP", [""])
        print("Drive motor finish")


#ui = UI()
