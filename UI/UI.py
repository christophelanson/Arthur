import tkinter as tk
from tkinter import ttk
import sys
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')
sys.path.insert(0, '../ExceptionFolder')
import RadioCommunication
import multiprocessing
import Motor
import ExceptionFile
import threading
import ctypes


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
            
            
class UI:

    def __init__(self, motor, communication, lidar, camera):

        self.motor = motor
        self.rc = communication
        self.lidar = lidar
        self.camera = camera
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
        self.pathLogId = self.fileReader.read("../Log/pathLogId.txt")
        self.fileReader.write("../Log/pathLogId.txt", str(int(self.pathLogId) + 1 ))
        self.pathLog = "../Log/log/"+self.pathLogId + ".txt"
        self.functionPara = ""
        self.commandMotor = ""
    
    def setThreadId(self, threadCommunicationId, threadmotorId):
        self.threadCommunicationId = threadCommunicationId
        self.threadmotorId = threadmotorId
        print("Thread Id set up")
        
    def runTK(self):
        self.root = tk.Tk()
        self.frm = ttk.Frame(self.root, padding=10)
        self.frm.grid()
        if self.isMaster:
            self.timeMove = tk.StringVar(self.root, self.timeMove)
            self.direction = tk.StringVar(self.root, self.direction)
            self.initSpeed = tk.StringVar(self.root, self.initSpeed)
            self.maxSpeed = tk.StringVar(self.root, self.maxSpeed)
            self.finalSpeed = tk.StringVar(self.root, self.finalSpeed)
            self.maxRotSpeed = tk.StringVar(self.root, self.maxRotSpeed)

            ttk.Label(self.frm, text="Motor Command!").grid(column=0, row=0)
            ttk.Button(self.frm, text="RUN", command=self.runMotorSend).grid(column=1, row=0)
            ttk.Button(self.frm, text="STOP", command=self.stopMotorSend).grid(column=1, row=1)
            ttk.Button(self.frm, text="TURN", command=self.turnMotorSend).grid(column=1, row=2)
            ttk.Button(self.frm, text="SCAN", command=self.scanSend).grid(column=1, row=3)
            ttk.Button(self.frm, text="PHOTO", command=self.cameraSend).grid(column=1, row=4)
            ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=1, row=5)

            ttk.Entry(self.frm, textvariable=self.timeMove).grid(column=2, row=0)
            ttk.Entry(self.frm, textvariable=self.direction).grid(column=2, row=1)
            ttk.Entry(self.frm, textvariable=self.initSpeed).grid(column=2, row=2)
            ttk.Entry(self.frm, textvariable=self.maxSpeed).grid(column=2, row=3)
            ttk.Entry(self.frm, textvariable=self.finalSpeed).grid(column=2, row=4)
            ttk.Entry(self.frm, textvariable=self.maxRotSpeed).grid(column=2, row=5)
            self.root.mainloop()
    
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
        
    def runMotorSend(self):
        #self.incrementFileNb()
        command = [self.rc.dictCommande["RUN"], int(self.timeMove.get()),
                   int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                   int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()), self.idCommand]
        print("Commande send:", command)
        self.commandMotor = command
        self.send(command)
        self.idCommand = not self.idCommand
        

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
