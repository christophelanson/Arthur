import os

class Camera:
    
    def __init__(self):
        self.photoPath = "../Log/Images/"
        self.isCapture = False
        self.numeroDeFichier = 0 
    
    def capture(self):
        os.system("raspistill -vf -hf -o "+self.photoPath+str(self.numeroDeFichier))
    
    def run(self):
        while True:
            if self.isCapture:
                self.capture()
                self.isCapture = False