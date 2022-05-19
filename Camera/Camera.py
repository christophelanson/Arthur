import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt


class Camera(QRunnable):
    
    def __init__(self, database):
        super(Camera, self).__init__()
        self.dataBase = database
        self.hardwareName = "camera"
        self.photoPath = "../Log/Images/"
        self.isCapture = False
        self.numeroDeFichier = 0 
    
        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "command":
            self.capture()
    

    @pyqtSlot()
    def run(self):
            print("Thread", self.hardwareName, "is running")
    
    def capture(self):
        os.system("raspistill -vf -q 100 -hf -o "+self.photoPath+str(self.numeroDeFichier))
    

if __name__ == "__main__":
    camera = Camera()
    camera.capture()
