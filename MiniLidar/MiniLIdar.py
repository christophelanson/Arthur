import RPi.GPIO as GPIO
import time

class MiniLidar:
    
    def __init__(self):
        self.port1 = 21
        self.isCounting = False
        self.timeStart = 0 
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.port1, GPIO.IN)
        
    def run(self):
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
                    time.sleep(1)
                    
                    
            else:
                if signal == 1:
                    self.timeStart = time.time()
                    self.isCounting = True
                    

            
if __name__ == "__main__":
    
    miniLidar = MiniLidar()
    miniLidar.run()