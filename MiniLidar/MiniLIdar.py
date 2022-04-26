import RPi.GPIO as GPIO
import time
from Mqtt import Mqtt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from DataBase import DataBase
from colorama import Fore
import random

class MiniLidar(QRunnable):
    
    def __init__(self):
        super(MiniLidar, self).__init__()
        self.hardwareName = "miniLidar"
        self.dataBase = DataBase.DataBase(id=self.hardwareName)
        self.port1 = 21
        self.isCounting = False
        self.timeStart = 0 
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setwarnings(False)
        #GPIO.setup(self.port1, GPIO.IN)

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        if self.mqtt.lastCommand == "getState":
            message = "state/" + self.state
            self.mqtt.sendMessage(message=message, receiver=self.mqtt.lastSender)
    
        if self.mqtt.lastCommand == "command":
            self.executeCommand(self.mqtt.lastPayload)
        
        if self.mqtt.lastCommand == "gyroValue":
            self.gyroValue = int(self.mqtt.lastPayload.split("-")[0])
        self.messageReceived = False
        
    @pyqtSlot()
    def run(self):
            print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> thread is running")
            while True:
                time.sleep(0.1)
                self.sendValue()
    
    @pyqtSlot()
    def stop(self):
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> thread is closed")
        exit(0)

    def sendValue(self):
        value = str(self.getSensorValue())
        self.dataBase.updateSensorValue("miniLidar", value)

    def getSensorValue(self):
        #return 345
        while True:
            signal = GPIO.input(self.port1)
            if self.isCounting:
                if signal == 0:
                    pulseWidth = (time.time() - self.timeStart)*1000000
                    print("pulseWidth:", pulseWidth)
                    distance = 2*(pulseWidth - 1000)
                    print("Distance:", distance)
                    self.isCounting = False
                    self.timeStart = 0
                    return distance
            else:
                if signal == 1:
                    self.timeStart = time.time()
                    self.isCounting = True
                    

            
if __name__ == "__main__":
    
    miniLidar = MiniLidar()
    miniLidar.run()