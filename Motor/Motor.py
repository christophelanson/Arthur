from fake_rpi.RPi import GPIO
import time
import numpy as np
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt
  
  
class Motor(QRunnable):

    def __init__(self, hardwareId):
        super(Motor, self).__init__()
        self.hardwareName = "motor"
        self.hardwareId = hardwareId

        self.isCommand = False
        self.command = []
        
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
        #self.gyro = Gyro.Compass()
        self.startDirection = 0
        self.state = "init"

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)


    def on_message(self, client, data, message):
        print("message topic:", message.topic)
        print("message", str(message.payload.decode()))


    @pyqtSlot()
    def run(self):
        while True:
            pass
            #if self.isCommand:
             #   self.executeCommand()
             #   self.isCommand = False
            #time.sleep(0.1)
            #self.state = "ready"    def get(self, command):
    
    def get(self, command):
        if command == "getState":
            return self.state


    def stop(self):
        self.pwm_ENA.stop()
        self.pwm_ENB.stop()
        self.listSpeed.append(0)
        self.listSpeedRight.append(0)
        self.listSpeedLeft.append(0)
        self.isStop = False
        self.state = "stop"
    
    def gyro(self,command):
        return self.messageRouter.route(senderName=self.node, receiverName=self.node, hardware="gyro", command=command, isReturn=False, channel="own")
    
    def calculateCorrectionRun(self, currentSpeed):
        currentDirection = self.gyro(command="COMPASS")
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

    def move(self, timeMove, direction, initSpeed, maxSpeed, finalSpeed):
        self.state = "running"
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

        #plt.figure()
       # plt.plot(self.listSpeedRight)
        #plt.plot(self.listSpeedLeft)

    def executeCommand(self):
        action = self.command[0]
        self.payload = self.command[1:]
        if action == self.messageRouter.dictCommand["RUN"]:
            self.move(self.payload[0], self.payload[1], self.payload[2], self.payload[3], self.payload[4])
        if action == self.messageRouter.dictCommand["TURN"]:
            self.move(self.payload[0], self.payload[1], self.payload[2], self.payload[3], self.payload[4], self.payload[5])
        if action == self.messageRouter.dictCommand["STOP"]:
            self.isStop = True
            

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

