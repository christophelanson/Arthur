from tkinter import *
from tkinter import ttk
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')
import RadioCommunication
import multiprocessing
import Motor

class manageProcess():
    
    def __init__(self, ui):
        self.isListenProcess = False
        self.ui = ui
    
    def run(self):
        while True:
            if self.isListenProcess == False :
                self.ui.listenPara()
                self.isListenProcess = True
                
class Process(multiprocessing.Process):
    
    def __init__(self, id, ui):
        super(Process, self).__init__()
        self.ui = ui
        self.id = id
        
    def run(self):
         
        if self.ui.functionPara == "manager":
            print("I'm the manager process with id: {}".format(self.id))
            self.ui.managerProcess.run()
            
        if self.ui.functionPara == "listen":
            print("I'm the listen process with id: {}".format(self.id))
            self.ui.messageReceive = self.ui.rc.listen()
            self.ui.decodeReiceivedMessage()
            self.ui.managerProcess.isListenProcess = False
            
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
        self.timeMove = 3
        self.direction = 1
        self.initSpeed = 0
        self.maxSpeed = 50
        self.finalSpeed = 0
        self.maxRotSpeed = 10
        self.oldPayload = []
        
        self.rc = RadioCommunication.RadioCommuncation(1)
        self.motor = Motor.Motor()
        self.managerProcess = manageProcess(self)
        self.managerProcessPara()

        self.functionPara = ""
        self.commandMotor = ""
        self.messageReceive = ""
    
        if self.isMaster:
            self.root = Tk()
            self.frm = ttk.Frame(self.root, padding=10)
            self.frm.grid()
            ttk.Label(self.frm, text="Motor Command!").grid(column=0, row=0)
            ttk.Button(self.frm, text="RUN", command=self.runPara).grid(column=1, row=0)
            ttk.Button(self.frm, text="STOP", command=self.stop).grid(column=1, row=2)
            ttk.Button(self.frm, text="TURN", command=self.turnPara).grid(column=1, row=2)
            ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=1, row=3)
            self.root.mainloop()
        else:
            pass
        
    
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
        command.append(int(self.timeMove))
        command.append(int(round(self.timeMove,2)%1))
        command.append(self.direction)
        command.append(self.initSpeed)
        command.append(self.maxSpeed)
        command.append(self.finalSpeed)
        command.append(self.idCommand)
        print("Commande send:",command)
        self.commandMotor = command
        self.rc.send(command)
        self.idCommand = not self.idCommand
    
    def turnPara(self):
        command = []
        command.append(self.rc.dictCommande["TURN"])
        command.append(int(self.timeMove))
        command.append(int(round(self.timeMove,2)%1))
        command.append(self.direction)
        command.append(self.initSpeed)
        command.append(self.maxSpeed)
        command.append(self.finalSpeed)
        command.append(self.maxRotSpeed)
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
                command = payload[2:]
                command[0] = payload[3] + payload[4]/100
                print("timeMove",command[0])
                print("direction",command[1])
                print("initSpeed",command[2])
                print("maxSpeed",command[3])
                print("finalSpeed",command[4])
                self.commandMotorPara( "RUN", command)
                
            if action == self.rc.dictCommande["TURN"]:
                command = payload[2:]
                command[0] = payload[3] + payload[4]/100
                print("timeMove",command[0])
                print("direction",command[1])
                print("initSpeed",command[2])
                print("maxSpeed",command[3])
                print("finalSpeed",command[4])
                print("maxSpeedRot",command[5])
                self.commandMotorPara( "TURN", command)
                self.listenPara()
                
            if action == self.rc.dictCommande["STOP"]:
                self.commandMotorPara( "STOP", [""])
                self.listenPara()
    

ui = UI()
