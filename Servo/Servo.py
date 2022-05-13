from __future__ import division
import numpy
from pybotics.predefined_models import ur10   #si robot.ik return None, modifier la fonction dans la librairie robot et return result (pas result.x)
from pybotics.robot import Robot
import time
import Adafruit_PCA9685
import RPi.GPIO as GPIO
import numpy as np
from pybotics.geometry import vector_2_matrix
from Mqtt import Mqtt

class PyboticsHandler:
    
    def __init__(self):
        self.robot = Robot.from_parameters(ur10())
    
    def calculateServoAngle(self, position):
        res = self.robot.ik(position)
        print(res)
        return res


class CardServo:
    
    def __init__(self):

        self.pwm = Adafruit_PCA9685.PCA9685(address=0x41)
        self.servo_min = 100  # Minimale Pulslaenge
        self.servo_max = 525  # Maximale Pulslaenge
        self.pwm.set_pwm_freq(50)

    def move(self, channel, pulse):
        #pulse_length = 1000000 
        #pulse_length /= 50     
        #pulse_length /= 4096     
        #pulse *= 1000
        #pulse /= pulse_length
        #pulse = round(pulse)
        pulse = int(pulse)
        print("pulse", pulse)
        self.pwm.set_pwm(channel, 0, pulse)

    def angle_to_pulse(self,angle):
        """
        return a pulse from an angle in degrees
        angle range from 0 to 180
        pulse range from servo_min to servo_max
        """
        pulse = self.servo_min + angle * (self.servo_max - self.servo_min)/180
        return pulse


class Servo(QRunnable):
    
    def __init__(self):
        super(Servo, self).__init__()
        self.pyboticsHandler = PyboticsHandler()
        self.cardServo = CardServo()

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0
        self.messageReceived = False

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        
    @pyqtSlot()
    def run(self):
            print("Thread", self.hardwareName, "is running")
    

    @pyqtSlot()
    def stop(self):
        print(self.hardwareName, "closed")
        exit(0)
    
    def calculateAngle(self, position):
        angles = self.pyboticsHandler.calculateServoAngle(position)
        return angles
    
    def servoControler(self, angles):
        for i, angle in enumerate(angles):
            print("angle", i, angle)
            self.cardServo.move(i, self.cardServo.angle_to_pulse(angle))
            #time.sleep(1.5)
    
    def move(self,position):
        angles = self.calculateAngle(position)
        print(angles)
        self.servoControler(angles)
        
        
if __name__ == "__main__":
    servo = Servo()
    #position =  vector_2_matrix([600, -150, 800, 100, 000, 0])
    #servo.move(position)
    angles=[90,120,100,100,90,30]
    servo.servoControler(angles)
    #servo.cardServo.move(2,1.6)