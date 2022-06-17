import RPi.GPIO as GPIO
import time
import numpy as np
from Message.MessageRouter import MessageRouter
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt
from DataBase import DataBase
from Gyro import Gyro
  
class Motor(QRunnable):

    def __init__(self):
        
        super(Motor, self).__init__()
        self.hardwareName = "motor"
        self.dataBase = DataBase.DataBase(id=self.hardwareName)
        self.gyro = Gyro.Compass()
        self.isStop = False
        self.INA = 26  #20 => 26
        self.INB = 6     #19 => 6
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
        # Set the PWM pin and frequency     [Errno 121] Remote I/O erroris 2000hz
        self.pwm_ENA = GPIO.PWM(self.ENA, 2000)
        self.pwm_ENB = GPIO.PWM(self.ENB, 2000)
        self.startDirection = 0
        self.state = "init"

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0
        self.messageReceived = False

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        print(self.mqtt.lastCommand,self.mqtt.lastPayload)
        if self.mqtt.lastCommand == "getState":
            message = "state/" + self.state
            self.mqtt.sendMessage(message=message, receiver=self.mqtt.lastSender)
    
        if self.mqtt.lastCommand == "command":
            self.executeCommand(self.mqtt.lastPayload)
            self.mqtt.sendMessage(message="return/1", receiver=self.mqtt.lastSender)
        
        

        if self.mqtt.lastCommand == "gyroValue":
            self.gyroValue = int(self.mqtt.lastPayload.split(",")[0])
        self.messageReceived = False
        
    @pyqtSlot()
    def run(self):
            print("Thread", self.hardwareName, "is running")
    

    @pyqtSlot()
    def stop(self):
        print(self.hardwareName, "closed")
        exit(0)

    def stop(self):
        self.pwm_ENA.stop()
        self.pwm_ENB.stop()
        self.listSpeed.append(0)
        self.listSpeedRight.append(0)
        self.listSpeedLeft.append(0)
        self.isStop = False
        self.state = "stop"
    
    def getGyroValue(self):
        #print(self.dataBase.getSensorValue("gyro"))
        #return float(self.dataBase.getSensorValue("gyro").split("-")[0])
        return float(self.gyro.getSensorValue().split(",")[0])
        
        #return self.messageRouter.route(senderName=self.node, receiverName=self.node, hardware="gyro", command=command, isReturn=False, channel="own")
        
    def calculateCorrectionRun(self, currentSpeed):
        currentDirection = self.getGyroValue()

        deltaCompass = self.startDirection - currentDirection

        if deltaCompass < -180:
            deltaCompass += 360
        elif deltaCompass > 180:
            deltaCompass -= 360

        correctionRun = (deltaCompass*5) / 180 # fonction à vérifier
        currentSpeedRight = currentSpeed * (1 - correctionRun)
        currentSpeedLeft = currentSpeed * (1 + correctionRun)
        #print(self.startDirection, currentDirection, currentSpeedLeft, currentSpeedRight)
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

    def move(self, timeMove, direction, initSpeed, maxSpeed, finalSpeed):
        self.state = "running"
        self.startDirection = self.getGyroValue()
        nominalTime = timeMove - (self.dT * 12)
        nbDtNominalTime = int(nominalTime / self.dT)
        addzero = list(np.zeros((nbDtNominalTime)))
        self.listStep = self.listStepUp + addzero + self.listStepDown
        currentSpeed = initSpeed
        for i, step in enumerate(self.listStep):
            if self.isStop:
                self.stop()
                break
            else:
                currentSpeed, currentSpeedLeft, currentSpeedRight = self.calculateSpeedRun(i, currentSpeed, maxSpeed)
                currentSpeedLeft = max(min(currentSpeedLeft,99),-99)
                currentSpeedRight = max(min(currentSpeedRight,99),-99)
                self.driveMotor(currentSpeedLeft, currentSpeedRight, self.dT, direction)
        self.stop()
        print("MOTOR STOP")

    def rotate(self, angle, speed):

        startDirection = self.getGyroValue()
        endDirection = (startDirection + angle)%360

        if (angle > 0):
            speedLeft  = speed
            speedRight = -speed
        else:
            speedLeft  = -speed
            speedRight = speed

        while (abs(endDirection - self.getGyroValue())%360) > 1:
            self.driveMotor(speedLeft, speedRight, 0.1, 1)
        self.stop()
        


    def turn(self, timeMove, direction, initSpeed, maxSpeed, finalSpeed, maxRotSpeed):
        self.state = "turning"
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

    def executeCommand(self, command):
        
        command = command.split(",")
        action = command[0]
        payload = command[1:]
        payload = [float(i) for i in payload]

        print(action, payload)
        if action == "run":
            print("Motor start run")
            self.move(payload[0], payload[1], payload[2], payload[3], payload[4])
        
        if action == "rotate":
            print("Motor rotating")
            self.rotate(payload[0], payload[1])

        if action == "TURN":
            print("Motor start turn")
            self.move(payload[0], payload[1], payload[2], payload[3], payload[4], payload[5])

        if action == "STOP":
            print("Motor stopped")
            self.stop
            

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

