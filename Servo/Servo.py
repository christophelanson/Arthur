from __future__ import division
import numpy
from pybotics.predefined_models import ur10   #si robot.ik return None, modifier la fonction dans la librairie robot et return result (pas result.x)
from pybotics.robot import Robot
import time
import Adafruit_PCA9685
import RPi.GPIO as GPIO
import numpy as np
from pybotics.geometry import vector_2_matrix


class PyboticsHandler:
    
    def __init__(self):
        self.robot = Robot.from_parameters(ur10())
    
    def calculateServoAngle(self, postion):
        res = self.robot.ik(position)
        print(res)
        return res


class CardServo:
    
    def __init__(self):

        self.pwm = Adafruit_PCA9685.PCA9685(address=0x41)
        servo_min = 150  # Minimale Pulslaenge
        servo_max = 600  # Maximale Pulslaenge
        self.pwm.set_pwm_freq(50)

    def move(self, channel, pulse):
        pulse_length = 1000000 
        pulse_length /= 50     
        pulse_length /= 4096     
        pulse *= 1000
        pulse /= pulse_length
        pulse = round(pulse)
        pulse = int(pulse)
        print("pulse", pulse)
        self.pwm.set_pwm(channel, 0, pulse)


    
class Servo:
    
    def __init__(self):
        self.pyboticsHandler = PyboticsHandler()
        self.cardServo = CardServo()
    
    def calculateAngle(self, postion):
        angles = self.pyboticsHandler.calculateServoAngle(postion)
        return angles
    
    def servoControler(self, angles):
        for i, angle in enumerate(angles):
            print("angle", i, angle)
            self.cardServo.move(i, angle)
            #time.sleep(1.5)
    
    def move(self,postion):
        angles = self.calculateAngle(position)
        print(angles)
        #self.servoControler(angles)
        
        
if __name__ == "__main__":
    servo = Servo()
    position =  vector_2_matrix([600, -150, 800, 0, 0, 0])
    servo.move(position)