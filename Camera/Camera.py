import os
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
print("hello")
class Camera(QRunnable):
    
    def __init__(self, messageRouter, hardwareId):
        super(Camera, self).__init__()
        self.messageRouter = messageRouter
        self.hardwareName = "camera"
        self.hardwareId = hardwareId
        self.photoPath = "../Log/Images/"
        self.isCapture = False
        self.numeroDeFichier = 0 
    
    def capture(self):
        os.system("raspistill -vf -hf -o "+self.photoPath+str(self.numeroDeFichier))
    
    def get(self, command):
        if command == "getState":
            return self.state

    @pyqtSlot()
    def run(self):
        while True:
            if self.isCapture:
                self.capture()
                self.isCapture = False

