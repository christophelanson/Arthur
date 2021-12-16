import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
import numpy as np
import math
import Gyro


class Motor:

    def __init__(self):
        self.isStop = False
        self.INA = 20
        self.INB = 19
        self.ENA = 16
        self.ENB = 13
        self.dT = 0.08
        self.Step = 0
        self.listStepUp = [1 / 12, 2 / 12, 3 / 12, 3 / 12, 2 / 12, 1 / 12]
        self.listStepDown =  [-1 / 12, -2 / 12, -3 / 12, -3 / 12, -2 / 12,-1 / 12]
        self.correctionTurn = 0
        self.listSpeed = []
        self.listSpeedRight = []
        self.listSpeedLeft = []
        # Set the GPIO port to BCM encoding mode.
        GPIO.setmode(GPIO.BCM)
        # Ignore warning information
        GPIO.setwarnings(False)
        GPIO.setup(self.ENA, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.INA, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.ENB, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.INB, GPIO.OUT, initial=GPIO.LOW)
        # Set the PWM pin and frequency is 2000hz
        self.pwm_ENA = GPIO.PWM(self.ENA, 2000)
        self.pwm_ENB = GPIO.PWM(self.ENB, 2000)

        self.isCommand = False
        self.func = ""
        self.command = []
        
        self.gyro = Gyro()
        self.startDirection = 0 

    def stop(self):
        self.pwm_ENA.stop()
        self.pwm_ENB.stop()
        self.listSpeed.append(0)
        self.listSpeedRight.append(0)
        self.listSpeedLeft.append(0)
        self.isStop = False
    
    def gyro(self):
        return self.gyro.run("COMPASS")
    
    def calculateCorrectionRun(self, currentSpeed):
        currentDirection = self.gyro()
        correctionRun = self.startDirection - currentDirection # fonction à vérifier
        currentSpeedRight = currentSpeed * (1 - correctionRun)
        currentSpeedLeft = currentSpeed * (1 + correctionRun)
        return currentSpeedLeft, currentSpeedRight

    def calculateCorrectionTurn(self, currentSpeedLeft, currentSpeedRight):
        currentSpeedRight = currentSpeedRight * (1 - self.correctionTurn)
        currentSpeedLeft = currentSpeedLeft * (1 + self.correctionTurn)
        return currentSpeedLeft, currentSpeedRight

    def calculateSpeedRun(self, step, currentSpeed, maxSpeed):
        currentSpeed = currentSpeed + (maxSpeed * self.listStep[step])
        currentSpeedLeft, currentSpeedRight = self.calculateCorrectionRun(currentSpeed)
        return currentSpeed, currentSpeedLeft, currentSpeedRight

    def calculateSpeedTurn(self, step, currentSpeedLeft, currentSpeedRight, speedLeft, speedRight):
        currentSpeedLeft = currentSpeedLeft + (speedLeft * self.listStep[step])
        currentSpeedRight = currentSpeedRight + (speedRight * self.listStep[step])
        currentSpeedLeft, currentSpeedRight = self.calculateCorrectionTurn(currentSpeedLeft, currentSpeedRight)
        return currentSpeedLeft, currentSpeedRight

    def driveMotor(self, currentSpeedLeft, currentSpeedRight, timeStep, direction):
        if currentSpeedLeft * direction < 0:
            GPIO.output(self.INA, GPIO.LOW)
        else:
            GPIO.output(self.INA, GPIO.HIGH)

        if currentSpeedRight * direction < 0:
            GPIO.output(self.INB, GPIO.LOW)
        else:
            GPIO.output(self.INB, GPIO.HIGH)

        self.pwm_ENA.start(abs(currentSpeedLeft))
        self.pwm_ENB.start(abs(currentSpeedRight))
        time.sleep(timeStep)

    def run(self, timeMove, direction, initSpeed, maxSpeed, finalSpeed):
        self.startDirection = self.gyro()
        nominalTime = timeMove - (self.dT * 12)
        nbDtNominalTime = int(nominalTime / self.dt)
        addzero = list(np.zeros((nbDtNominalTime)))
        self.listStep = self.listStepUp + addzero + self.listStepDown
        currentSpeed = initSpeed
        for i, step in enumerate(self.listStep):
            if self.isStop:
                self.stop()
                break
            else:
                currentSpeed, currentSpeedLeft, currentSpeedRight = self.calculateSpeedRun(i, currentSpeed, maxSpeed)
                #self.listSpeed.append(currentSpeed)
                #self.listSpeedRight.append(currentSpeedRight)
                #self.listSpeedLeft.append(currentSpeedLeft)
                #timeStep = nominalTime if self.listStep[i] == 0 else self.dT
                self.driveMotor(currentSpeedLeft, currentSpeedRight, self.dT, direction)
        self.stop()

        plt.figure()
        plt.plot(self.listSpeed)
        plt.plot(self.listSpeedRight)
        plt.plot(self.listSpeedLeft)

    def turn(self, timeMove, direction, initSpeed, maxSpeed, finalSpeed, maxRotSpeed):
        speedLeft = maxSpeed + maxRotSpeed
        speedRight = maxSpeed - maxRotSpeed

        if speedLeft > 90:  # pas de vitesse supérieure à 90
            timeMove = timeMove * (speedLeft / 90)
            speedRight = speedRight * (90 / speedLeft)
            speedLeft = 90

        if speedRight > 90:  # pas de vitesse supérieure à 90
            timeMove = timeMove * (speedRight / 90)
            speedLeft = speedLeft * (90 / speedRight)
            speedRight = 90

        if timeMove < (self.dT * 12):  # augmentation du temps et réduction de la vitesse
            speedLeft = speedLeft * (timeMove / (self.dT * 12))
            speedRight = speedRight * (timeMove / (self.dT * 12))
            timeMove = self.dt * 12

        nominalTime = timeMove - (self.dT * 12)
        currentSpeedRight = initSpeed
        currentSpeedLeft = initSpeed
        for i, step in enumerate(self.listStep):
            if self.isStop:
                self.stop()
                break
            else:
                currentSpeedLeft, currentSpeedRight = self.calculateSpeedTurn(i, currentSpeedLeft, currentSpeedRight, speedLeft, speedRight)
                self.listSpeedRight.append(currentSpeedRight)
                self.listSpeedLeft.append(currentSpeedLeft)
                timeStep = nominalTime if self.listStep[i] == 0 else self.dT
                self.driveMotor(currentSpeedLeft, currentSpeedRight, timeStep, direction)
        self.stop()

        #plt.figure()
       # plt.plot(self.listSpeedRight)
        #plt.plot(self.listSpeedLeft)

    def decoderCommand(self):
        if self.func == "RUN":
            self.run(self.command[0], self.command[1], self.command[2], self.command[3], self.command[4])
        if self.func == "TURN":
            self.turn(self.command[0], self.command[1], self.command[2], self.command[3], self.command[4], self.command[5])
        if self.func == "STOP":
            self.isStop = True

    def runProcess(self):
        while True:
            if self.isCommand:
                self.decoderCommand()
                self.isCommand = False
            time.sleep(0.1)


if __name__ == "__main__":
    motor = Motor()
    #motor.run(6, 1, 0, 40, 0)
    motor.turn(4, 1, 0, 40, 0, 0)


    # motor.stop()
    # try:
    #     pass
    # except KeyboardInterrupt:
    #     motor.stop()
    #     GPIO.cleanup()
    #
    #motor.stop()
    #GPIO.cleanup()

