from __future__ import division
import Adafruit_PCA9685
import RPi.GPIO as GPIO
import numpy as np
from colorama import Fore
    
class Servo:
    
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
        print(f"{Fore.GREEN}INFO (Servo) -> pulse : {pulse}")
        self.pwm.set_pwm(channel, 0, pulse)

    def getCurrentPulsesFromMemory(self, channel):
        pulse = self.pwm.read_pwm(channel=channel)
        print(f"{Fore.GREEN}INFO (Servo) -> Pulse read in memory {pulse}, at channel {channel} ")
        return pulse

    def getAllPulsesFromMemory(self, nbServos=6):
        for i in range(nbServos):
            self.getCurrentPulsesFromMemory(i)

    def angle_to_pulse(self,angle):
        """
        return a pulse from an angle in degrees
        angle range from 0 to 180
        pulse range from servo_min to servo_max
        """
        pulse = self.servo_min + angle * (self.servo_max - self.servo_min)/180
        return pulse

    def servoControler(self, angles):
        for i, angle in enumerate(angles):
            print(f"{Fore.GREEN}INFO (Servo) -> angle {i} : {angle} ")
            self.move(i, self.angle_to_pulse(angle))
        
        
if __name__ == "__main__":
    servo = Servo()
    servo.getAllPulsesFromMemory()
    angles=[70,100,100,100,90,80]
    servo.servoControler(angles)
    #servo.getAllPulsesFromMemory()
    