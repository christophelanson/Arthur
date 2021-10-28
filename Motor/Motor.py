#import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np
import math


class Motor:

    def __init__(self):
        self.INA = 20
        self.INB = 19
        self.ENA = 16
        self.ENB = 13
        self.dT = 0.01
        self.Step = 0
        self.listStep = [1/12, 2/12, 3/12, 3/12, 2/12, 1/12, 0, -1/12, -2/12, -3/12, -3/12, -2/12, -1/12]
        self.correctionLeft = -0
        self.correctionRight = 0
        self.l = 10
        self.listSpeed = []
        self.listSpeedRight = []
        self.listSpeedLeft = []
        # Set the GPIO port to BCM encoding mode.
        #GPIO.setmode(GPIO.BCM)
        # Ignore warning information
        #GPIO.setwarnings(False)
        #GPIO.setup(self.ENA, GPIO.OUT, initial=GPIO.HIGH)
        #GPIO.setup(self.INA, GPIO.OUT, initial=GPIO.LOW)
        #GPIO.setup(self.ENB, GPIO.OUT, initial=GPIO.HIGH)
        #GPIO.setup(self.INB, GPIO.OUT, initial=GPIO.LOW)
        self.pwm_ENA = GPIO.PWM(self.ENA, 2000)
        self.pwm_ENB = GPIO.PWM(self.ENB, 2000)
        
    def stop(self):
        self.pwm_ENA.stop()
        self.pwm_ENB.stop()
        self.listSpeed.append(0)
        self.listSpeedRight.append(0)
        self.listSpeedLeft.append(0)

    def calculateCorrection(self, currentSpeed):
        currentSpeedRight = currentSpeed + self.correctionRight
        currentSpeedLeft = currentSpeed + self.correctionLeft
        return currentSpeedLeft, currentSpeedRight

    def calculateSpeed(self, step, currentSpeed, maxSpeed):
        currentSpeed = currentSpeed + (maxSpeed * self.listStep[step])
        currentSpeedLeft, currentSpeedRight = self.calculateCorrection(currentSpeed)
        return currentSpeed, currentSpeedLeft, currentSpeedRight

    def calculateCorrectionAngle(self, currentSpeedLeft, currentSpeedRigth):
        currentSpeedRight = currentSpeedRigth + self.correctionRight
        currentSpeedLeft = currentSpeedLeft + self.correctionLeft
        return currentSpeedLeft, currentSpeedRight

    def calculateSpeedAngle(self, step, currentSpeedLeft, currentSpeedRight, speedLeft, speedRight):
        currentSpeedLeft = currentSpeedLeft + (speedLeft * self.listStep[step])
        currentSpeedRigth = currentSpeedRight + (speedRight * self.listStep[step])
        currentSpeedLeft, currentSpeedRight = self.calculateCorrectionAngle(currentSpeedLeft, currentSpeedRigth)
        return currentSpeedLeft, currentSpeedRight

    def driveMotor(self, currentSpeedLeft, currentSpeedRight, timeStep, dir):
        GPIO.output(self.INA, GPIO.HIGH)
        GPIO.output(self.INB, GPIO.HIGH)
        self.pwm_ENA.start(currentSpeedLeft)
        self.pwm_ENB.start(currentSpeedRight)
        time.sleep(timeStep)

    def run(self, timeMove, dir, initSpeed, maxSpeed, finalSpeed):
        nominalTime = timeMove - (self.dT * 12)
        currentSpeed = initSpeed
        for i, step in enumerate(self.listStep):
            currentSpeed, currentSpeedLeft, currentSpeedRight = self.calculateSpeed(i, currentSpeed, maxSpeed)
            self.listSpeed.append(currentSpeed)
            self.listSpeedRight.append(currentSpeedRight)
            self.listSpeedLeft.append(currentSpeedLeft)
            if self.listStep[0] == 0:
                timeStep = nominalTime
            else:
                timeStep = self.dT
            self.driveMotor(currentSpeedLeft, currentSpeedRight, timeStep, dir)
        self.stop()

        plt.figure()
        plt.plot(self.listSpeed)
        plt.plot(self.listSpeedRight)
        plt.plot(self.listSpeedLeft)
        plt.show()

    def turn(self, timeMove, dir, initSpeed, maxSpeed, finalSpeed, angle):
        angle = angle * (math.pi/180)
        speedLeft = maxSpeed + ((angle*(self.l/2))/timeMove)
        speedRight = maxSpeed - ((angle * (self.l / 2)) / timeMove)
        nominalTime = timeMove - (self.dT * 12)
        currentSpeedRight = initSpeed
        currentSpeedLeft = initSpeed
        for i, step in enumerate(self.listStep):
            currentSpeedLeft, currentSpeedRight = self.calculateSpeedAngle(i, currentSpeedLeft, currentSpeedRight, speedLeft, speedRight)
            self.listSpeedRight.append(currentSpeedRight)
            self.listSpeedLeft.append(currentSpeedLeft)
            if self.listStep[0] == 0:
                timeStep = nominalTime
            else:
                timeStep = self.dT
            self.driveMotor(currentSpeedLeft, currentSpeedRight, timeStep, dir)
        self.stop()

        plt.figure()
        plt.plot(self.listSpeedRight)
        plt.plot(self.listSpeedLeft)
        plt.show()
    
    def driveMotor(self,func, command):
        if func == "run":
            self.run(command[0], command[1], command[2], command[3], command[4])
        if func == "angle":
            self.turn(command[0], command[1], command[2], command[3], command[4], command[5])
        if func == "stop":
            self.stop


# motor = Motor()
# #motor.run(1, 1, 0, 100, 0)
# motor.turn(1, 1, 0, 50, 0, 90)
# try:
#     pass
# except KeyboardInterrupt:
#     motor.stop()
#     #GPIO.cleanup()

