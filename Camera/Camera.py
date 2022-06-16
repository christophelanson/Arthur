import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt


class Camera(QRunnable):
    
    def __init__(self): #, database):
        super(Camera, self).__init__()
        #self.dataBase = database
        self.hardwareName = "camera"
        self.photoPath = "./Log/Images/"
        self.isCapture = False
    
        self.listChannel = ["all"]        
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        if self.mqtt.lastCommand == "command":
            self.capture(self.mqtt.lastPayload)
    

    @pyqtSlot()
    def run(self):
            print("Thread", self.hardwareName, "is running")
    
    def capture(self,fileName="test"):
        os.system(f"raspistill -rot 270 -q 10 -t 1000 -o {self.photoPath}{fileName}.jpg")

    

if __name__ == "__main__":
    camera = Camera()
    camera.capture("test")
