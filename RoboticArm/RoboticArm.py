import sys
import os
sys.path.insert(0, './Servo')

import json
import math
import numpy as np
import Servo
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt

class RoboticArm(QRunnable):
    
    def __init__(self):

        super(RoboticArm, self).__init__()
        self.hardwareName = "roboticArm"
        # définition des paramètres du bras
        # loading robotID.json
        with open('robotID.json') as jsonFile:
            data = json.load(jsonFile)
        self.dSE = data['roboticArm']['dSE'] # distance shoulder-elbow en mm
        self.dEW = data['roboticArm']['dEW'] # distance elbow-wrist en mm
        self.dWMa = data['roboticArm']['dWMa'] # coude de la pince (perpendiculairement à la pince) en mm
        self.dWMd = data['roboticArm']['dWMd'] # longueur de la pince en mm
        self.dWM = math.sqrt(self.dWMa**2 + self.dWMd**2)
        self.correctionAngles = data['roboticArm']['correctionAngles'] # corrections dues à l'imprécision des servos

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

        self.gyroValue = 0
        self.messageReceived = False

        self.servo = Servo.Servo()

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
    
        if self.mqtt.lastCommand == "command":
            listPosition=self.mqtt.lastPayload.split(",")
            position=[]
            for value in listPosition:
                position.append(float(value))
            print(listPosition)
            angles = self.calculateAngles(position)
            if not angles:
                return
            print(angles)
            angles = np.asarray(angles)
            self.servo.servoControler(angles)
            self.mqtt.sendMessage(message="return/1", receiver=self.mqtt.lastSender)
        
    @pyqtSlot()
    def run(self):
            print("Thread", self.hardwareName, "is running")
    
    @pyqtSlot()
    def stop(self):
        print(self.hardwareName, "closed")
        exit(0)

    def calculateAngles(self,position):
        
        directionBras = position[0] # en degrés, dans le plan horizontal
        xM = position[1]
        zM = position[2]
        dSM = math.sqrt(xM**2 + zM**2)
        anglexSM = math.atan2(zM,xM) # angle SM par rapport à l'axe des x en radians
        incidencePince = position[3]/180 * math.pi # conversion en radians
        rotationPince = position[4] # en degrés
        ouverturePince = position[5] # en degrés
        # calcul des coordonnées xW et xZ de W dans la plan du bras
        xW = xM + self.dWMa*math.sin(incidencePince) - self.dWMd*math.cos(incidencePince)
        zW = zM - self.dWMa*math.cos(incidencePince) - self.dWMd*math.sin(incidencePince)
        dSW = math.sqrt(xW**2 + zW**2)
        anglexSW = math.atan2(zW,xW) # angle SW par rapport à l'axe des x en radians
            
        # vérification de l'existence d'une solution
        # condition dSM <= dSE + dEW + dWM : condition du bras tendu
        if dSM > self.dSE + self.dEW + self.dWM :
            print("Le bras est trop court pour atteindre l'objet")
            return False
        # condition sur l'incidence
        # calcul des incidences min et max
        dSWMax = self.dSE + self.dEW
        beta = math.acos((self.dWM**2 + dSM**2 - dSWMax**2)/2/self.dWM/dSM)
        gamma = math.atan2(self.dWMa,self.dWMd)
        incidenceMin = anglexSM - beta - gamma
        incidenceMax = anglexSM + beta - gamma
        print("incidenceMin =", round(incidenceMin/math.pi*180,1), "incidenceMax =", round(incidenceMax/math.pi*180,1))
        # condition
        if incidencePince < incidenceMin :
            print("L'angle d'incidence de la pince est trop faible")
            return False
        if incidencePince > incidenceMax :
            print("L'angle d'incidence de la pince est trop élevé")
            return False
        # condition sur la longeur de SW : SW <= SE + EW
        if dSW > dSWMax :
            print("Le bras est trop court pour atteindre l'objet")
            return False
        
        # calcul des angles des servos S, E et W
        angleWSE = math.acos((self.dSE**2 + dSW**2 - self.dEW**2)/2/self.dSE/dSW)
        angleSEW = math.acos((self.dSE**2 + self.dEW**2 - dSW**2)/2/self.dSE/self.dEW)
        angleEWS = math.pi - angleWSE - angleSEW
        
        #ces angles dépendent de du sens de rotation et de l'angle d'origine de chaque servo, constantes à ajouter le cas échéant selon chaque bras
        # formule initiale angleS = math.pi - (anglexSW + angleWSE) >>> devient pi - angleS
        angleS = math.pi - (anglexSW + angleWSE) # angle = 50° = contact avec la boite, angle = 180° = bras tendu vers l'avant
        # formule initiale angleE = angleSEW - math.pi/2 >>> devient angleE
        angleE = angleSEW # angle = 170° = reste du bras dans l'axe de SE
        # formule initiale angleW = math.pi + incidencePince + angleEWS - anglexSW  >>> reste identique
        angleW =  math.pi + incidencePince + angleEWS - anglexSW # angle = 0° = pince repliée vers le bas le long du bras, angle = 180° = dans l'axe de EW
        
        #conversion en degrés
        angleS = angleS * 180/math.pi
        angleE = angleE * 180/math.pi
        angleW = angleW * 180/math.pi
        
        angles = [directionBras, angleS, angleE, angleW, rotationPince, ouverturePince] # en degrés
        angles = [angles[i] + self.correctionAngles[i] for i in range(6)] # application de la correction servos
        return angles
    
        
if __name__ == "__main__":
    roboticArm = RoboticArm()
    position = [90,200,-100,-80,90,70] # position du point M à atteindre [directionBras(degrés), xM(mm), zM(mm), incidencePince(degrés), rotationPince(degrés), ouverturePince(degrés)]
    angles = roboticArm.calculateAngles(position)
    print(angles)
    angles = np.asarray(angles)
    #angles = [92,76+8,165-15,42-8,98,88]
    servo = Servo.Servo()
    servo.servoControler(angles)