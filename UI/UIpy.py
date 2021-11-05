from tkinter import *
import tkinter as tk
from tkinter import ttk
import sys
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')
import RadioCommunication
import multiprocessing
import Motor

class fileReader:
    
    def read(self, name):
        with open(name, "r") as fichier:
            return fichier.read()
    
    def write(self, name, data):
        with open(name, "w") as fichier:
            fichier.write(data)
            
class manageProcess():
    
    def __init__(self, ui):
        self.ui = ui
        self.fileReader = fileReader()
        self.fileReader.write("isListenProcess.txt","0")
    
    def run(self):
        while True:
            isListenProcess = self.fileReader.read("isListenProcess.txt")
            if isListenProcess == "0" :
                self.fileReader.write("isListenProcess.txt","1")
                self.ui.listenPara()
                
                
    def createListen(self):
        print("Listen process created")
        self.ui.listenPara()
                
class Process(multiprocessing.Process):
    
    def __init__(self, id, ui):
        super(Process, self).__init__()
        self.ui = ui
        self.id = id
        self.fileReader = fileReader()
        
    def run(self):
         
        if self.ui.functionPara == "manager":
            print("I'm the manager process with id: {}".format(self.id))
            self.ui.managerProcess.run()
            
        if self.ui.functionPara == "listen":
            print("I'm the listen process with id: {}".format(self.id))
            self.ui.messageReceive = self.ui.rc.listen()
            self.ui.decodeReiceivedMessage()
            self.fileReader.write("isListenProcess.txt","0")
            
        if self.ui.functionPara == "send":
            print("I'm the send process with id: {}".format(self.id))
            self.ui.rc.send(self.ui.commandMotor)
        
        if self.ui.functionPara == "driveMotor":
            print("I'm the drive motor process with id: {}".format(self.id))
            self.ui.motor.receiverCommand(self.ui.funcDriveMotor,self.ui.DriveMotorCommand)

class UI:
    
    def __init__(self):

        self.isMaster = True
        self.id_process = 0
        self.idCommand = False
        self.idReceived = None
        self.oldPayload = []
        self.isListenProcess = False
        self.timeMove = 4
        self.direction = 1
        self.initSpeed = 0
        self.maxSpeed = 60
        self.finalSpeed = 0
        self.maxRotSpeed = 40
        self.rc = RadioCommunication.RadioCommuncation(1)
        self.motor = Motor.Motor()
        self.managerProcess = manageProcess(self)
        self.managerProcessPara()

        self.functionPara = ""
        self.commandMotor = ""
        self.messageReceive = ""
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
            ttk.Button(self.frm, text="RUN", command=self.runPara).grid(column=1, row=0)
            ttk.Button(self.frm, text="STOP", command=self.stop).grid(column=1, row=1)
            ttk.Button(self.frm, text="TURN", command=self.turnPara).grid(column=1, row=2)
            ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=1, row=3)
            
            ttk.Entry(self.frm, textvariable=self.timeMove).grid(column=2, row=0)
            ttk.Entry(self.frm, textvariable=self.direction).grid(column=2, row=1)
            ttk.Entry(self.frm, textvariable=self.initSpeed).grid(column=2, row=2)
            ttk.Entry(self.frm, textvariable=self.maxSpeed).grid(column=2, row=3)
            ttk.Entry(self.frm, textvariable=self.finalSpeed).grid(column=2, row=4)
            ttk.Entry(self.frm, textvariable=self.maxRotSpeed).grid(column=2, row=5)
            self.root.mainloop()
        else:
            self.listenPara()

    def generateParaFunction(self, funcName):
        self.functionPara = funcName
        p = Process(self.id_process, self)
        p.start()
        self.id_process += 1
    
    def managerProcessPara(self):
        self.generateParaFunction("manager")
        
    def listenPara(self):
        self.generateParaFunction("listen")

    def runPara(self):
        command = []
        command.append(self.rc.dictCommande["RUN"])
        command.append(int(self.timeMove.get()))
        command.append(int(round(float(self.timeMove.get()),2)%1*100))
        command.append(int(self.direction.get()))
        command.append(int(self.initSpeed.get()))
        command.append(int(self.maxSpeed.get()))
        command.append(int(self.finalSpeed.get()))
        command.append(self.idCommand)
        print("Commande send:",command)
        self.commandMotor = command
        self.rc.send(command)
        self.idCommand = not self.idCommand
    
    def turnPara(self):
        command = []
        command.append(self.rc.dictCommande["TURN"])
        command.append(int(self.timeMove.get()))
        command.append(int(round(float(self.timeMove.get()),2)%1*100))
        command.append(int(self.direction.get()))
        command.append(int(self.initSpeed.get()))
        command.append(int(self.maxSpeed.get()))
        command.append(int(self.finalSpeed.get()))
        command.append(int(self.maxRotSpeed.get()))
        command.append(self.idCommand)
        print("Commande sent:",command)
        self.commandMotor = command
        self.rc.send(command)
        self.idCommand = not self.idCommand
    
    def stop(self):
        command = []
        command.append(self.rc.dictCommande["STOP"])
        command.append(self.idCommand)
        self.rc.send(command)
        self.idCommand = not self.idCommand
        
    def commandMotorPara(self, funcDriveMotor, DriveMotorCommand):
        if funcDriveMotor == "RUN":
            self.funcDriveMotor = "RUN"
            self.DriveMotorCommand = DriveMotorCommand
            self.generateParaFunction("driveMotor")
            
        if funcDriveMotor == "TURN":
            self.funcDriveMotor = "TURN"
            self.DriveMotorCommand = DriveMotorCommand
            self.generateParaFunction("driveMotor")
            
        if funcDriveMotor == "STOP":
            self.funcDriveMotor = "STOP"
            self.DriveMotorCommand = DriveMotorCommand
            self.generateParaFunction("driveMotor")
            
    def decodeReiceivedMessage(self):
        payload = []
        for i, data in enumerate(self.messageReceive):
            payload.append(int(hex(ord(data)),16))
        if payload[0] != 0 and payload[-1] != 64:
            print("erreur with payload received, first or last char wrong")
        else:
            # evite les redondances de commandes
            if payload == self.oldPayload:
                return 
            self.oldPayload = payload
            
            payload = payload[2:-1]
            action = payload[0]
            print("action", action )
            if action == self.rc.dictCommande["RUN"]:
                payload[2] = payload[1] + payload[2]/100
                payload = payload[2:]
                print("timeMove",payload[0], end=" ")
                print("direction",payload[1], end=" ")
                print("initSpeed",payload[2], end=" ")
                print("maxSpeed",payload[3], end=" ")
                print("finalSpeed",payload[4], end=" ")
                self.commandMotorPara( "RUN", payload)
                
            if action == self.rc.dictCommande["TURN"]:
                payload[2] = payload[1] + payload[2]/100
                payload = payload[2:]
                print("timeMove",payload[0], end=" ")
                print("direction",payload[1], end= " ")
                print("initSpeed",payload[2], end=" ")
                print("maxSpeed",payload[3], end=" ")
                print("finalSpeed",payload[4], end=" ")
                print("maxSpeedRot",payload[5])
                self.commandMotorPara( "TURN", payload)
                
            if action == self.rc.dictCommande["STOP"]:
                self.commandMotorPara( "STOP", [""])
        print("Drive motor finish")

ui = UI()

