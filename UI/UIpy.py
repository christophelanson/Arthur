from tkinter import *
from tkinter import ttk
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')
import RadioCommunication
import multiprocessing 

class Process(multiprocessing.Process):
    
    def __init__(self, id, ui):
        super(Process, self).__init__()
        self.ui = ui
        self.id = id
        
    def run(self):
         
        if self.ui.functionPara == "listen":
            print("I'm the listen process with id: {}".format(self.id))
            self.ui.messageReceive = self.ui.rc.listen()
            self.ui.decodeReiceivedMessage()
        
        if self.ui.functionPara == "send":
            print("I'm the send process with id: {}".format(self.id))
            self.ui.rc.send(self.ui.commandMotor)
        
        if self.ui.functionPara == "driveMotor":
            print("I'm the drive motor process with id: {}".format(self.id))
            self.ui.motor.send(self.ui.funcDriveMotor,self.ui.DriveMotorCommand)

class UI:
    
    def __init__(self):

        self.isMaster = True
        self.id_process = 0 
        self.timeMove = 3
        self.direction = 1
        self.initSpeed = 0
        self.maxSpeed = 50
        self.finalSpeed = 0
        self.angle = 90 
        self.rc = RadioCommunication.RadioCommuncation(1)
        self.motor = Motor.Motor()
        #self.listenPara()
        self.functionPara = ""
        self.commandMotor = ""
        self.messageReceive = ""
        if self.isMaster:
            self.root = Tk()
            self.frm = ttk.Frame(self.root, padding=10)
            self.frm.grid()
            ttk.Label(self.frm, text="Motor Command!").grid(column=0, row=0)
            ttk.Button(self.frm, text="Run", command=self.runPara).grid(column=1, row=0)
            ttk.Button(self.frm, text="Stop", command=self.root.destroy).grid(column=1, row=2)
            ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=1, row=3)
            self.root.mainloop()
        else:
            pass
    
    def generateParaFunction(self, funcName):
        self.functionPara = funcName
        p = Process(self.id_process, self)
        p.start()
        self.id_process += 1
        
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
        print("Commande send:",command)
        self.commandMotor = command
        self.rc.send(command)
        #self.generateParaFunction("send")
    
    def commandMotorPara(self, funcDriveMotor, DriveMotorCommand):
        self.funcDriveMotor = "Run"
        self.DriveMotorCommand = DriveMotorCommand
        self.generateParaFunction("driveMotor")
        
    def decodeReiceivedMessage(self):
        payload = []
        for i, data in enumerate(self.messageReceive):
            payload.append(int(hex(ord(data)),16))
        if payload[0] != 0 and payload[0] != 64:
            print("erreur with payload received, first or last char wrong")
        else:
            payload = payload[2:-1]
            action = payload[0]
            print("action", action )
            if action == self.rc.dictCommande["RUN"]:
                command = payload[2:]
                command[0] = payload[3] + payload[24]/100
                print("timeMove",command[0])
                print("direction",command[1])
                print("initSpeed",command[2])
                print("maxSpeed",command[3])
                print("finalSpeed",command[4])
                self.commandMotorPara(self, "run", command)
    

ui = UI()
