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


class UI:

    def __init__(self, motor, communication):

        self.motor = motor
        self.rc = communication
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

        self.functionPara = ""
        self.commandMotor = ""
        self.messageReceive = ""

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
            ttk.Button(self.frm, text="Quit", command=self.root.destroy).grid(column=1, row=3)

            ttk.Entry(self.frm, textvariable=self.timeMove).grid(column=2, row=0)
            ttk.Entry(self.frm, textvariable=self.direction).grid(column=2, row=1)
            ttk.Entry(self.frm, textvariable=self.initSpeed).grid(column=2, row=2)
            ttk.Entry(self.frm, textvariable=self.maxSpeed).grid(column=2, row=3)
            ttk.Entry(self.frm, textvariable=self.finalSpeed).grid(column=2, row=4)
            ttk.Entry(self.frm, textvariable=self.maxRotSpeed).grid(column=2, row=5)
            self.root.mainloop()

    def runMotorSend(self):
        command = [self.rc.dictCommande["RUN"], int(self.timeMove.get()),
                   int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                   int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()), self.idCommand]
        print("Commande send:", command)
        self.commandMotor = command
        self.rc.send(command)
        self.idCommand = not self.idCommand

    def turnMotorSend(self):
        command = [self.rc.dictCommande["TURN"], int(self.timeMove.get()),
                   int(round(float(self.timeMove.get()), 2) % 1 * 100), int(self.direction.get()),
                   int(self.initSpeed.get()), int(self.maxSpeed.get()), int(self.finalSpeed.get()),
                   int(self.maxRotSpeed.get()), self.idCommand]
        print("Commande sent:", command)
        self.commandMotor = command
        self.rc.send(command)
        self.idCommand = not self.idCommand

    def stopMotorSend(self):
        command = [self.rc.dictCommande["STOP"], self.idCommand]
        self.rc.send(command)
        self.idCommand = not self.idCommand

    def commandMotorReceived(self, funcDriveMotor, DriveMotorCommand):
        self.motor.func = funcDriveMotor
        self.motor.command = DriveMotorCommand
        self.motor.isCommand = True

    def decodeReiceivedMessage(self):
        payload = []
        for i, data in enumerate(self.messageReceive):
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
            if action == self.rc.dictCommande["RUN"]:
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                self.commandMotorReceived("RUN", payload)

            if action == self.rc.dictCommande["TURN"]:
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                print("maxSpeedRot", payload[5])
                self.commandMotorReceived("TURN", payload)

            if action == self.rc.dictCommande["STOP"]:
                self.commandMotorReceived("STOP", [""])
        print("Drive motor finish")


ui = UI()
