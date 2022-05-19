import serial
import math
import csv
import numpy as np
import time

from Mqtt import Mqtt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from DataBase import DataBase
from colorama import Fore
import random


class Lidar(QRunnable):
    
    def __init__(self): #, messageRouter):
        super(Lidar, self).__init__()
        self.hardwareName = "lidar"
        #self.dataBase = DataBase.DataBase(id=self.hardwareName)
        self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate='115200') #/dev/ttyUSB0
        self.ser.close()
        self.dict_angle_distance = {} # dictionnaire angles et distances classés par paquets angulaire d'amplitude 0,5° : dimension 720 lignes
        self.outputDataList = [] # liste de données collectées sans classement par paquet : dimension 7.200 lignes
        # [angle (degrés), distance (mm), scoreAvant (0 à 5), scoreArrière (0 à 5), scoreDébut objet (-10 à 10), scoreFin objet (-10 à 10), dDébutObjet (0/1), finObjet (0/1)]
             
        self.listObjets = [] # liste des objets [index, angle départ, distance départ, angle fin, distance fin]
        self.nbDonneesACollecter = 7200
        self.filtreEcartDistance = 100 #mm, écart de distance nécessaire pour changer d'objet
        self.seuilEcart = 6 # score de discontinuité à atteindre pour détecter un objet (début ou fin), cf. document protocole
        self.correctionAngle0 = 192.25 #correction d'angle pour que angle = 0 => avant du robot
        self.numeroDeFichier = 0
        self.isScan = False
        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        if self.mqtt.lastCommand == "getState":
            message = "state/" + self.state
            self.mqtt.sendMessage(message=message, receiver=self.mqtt.lastSender)
    
        if self.mqtt.lastCommand == "command":
            self.executeCommand(self.mqtt.lastPayload)
        
        if self.mqtt.lastCommand == "gyroValue":
            self.gyroValue = int(self.mqtt.lastPayload.split("-")[0])
        self.messageReceived = False
        
    @pyqtSlot()
    def run(self):
            print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> thread is running")
            # while True:
            #     self.dataBase.updateSensorValue("gyro", str(random.randrange(10)))
            #     time.sleep(0.1)
    
    @pyqtSlot()
    def stop(self):
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> thread is closed")
        exit(0)

    def executeCommand(self, payload):
        if payload == "scan":
            print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> Start scan")
            self.getData()
            self.createOutputDataList()

# fonction de calcul des scores Avant et Arrière, cf. doc protocole Lidar
    def CalculScores(self):
        listScores=[]
        for i, dataAngleDistance in enumerate(self.outputDataList):
            scoreAvant = 0
            scoreArriere = 0
            if i>=len(self.outputDataList)-1 - 5:
                scoreAvant=5
            else:
                for j in range(1,6):
                    if abs(dataAngleDistance[1]-self.outputDataList[i+j][1])<self.filtreEcartDistance :
                        scoreAvant += 1
            if i<=4:
                scoreArriere = 5
            else:
                for j in range(1,6):
                    if abs(dataAngleDistance[1]-self.outputDataList[i-j][1])<self.filtreEcartDistance:
                        scoreArriere += 1
            listScores.append([scoreAvant,scoreArriere])
        listScores=np.asarray(listScores)
        return listScores
    
    def getData(self):
        self.ser.open()
        # Début de la collecte des données Lidar
        dataCount = 0 # compteur de données collectées (angle, distance)
        data = []
        data_start = False
        self.outputDataList = []
        self.listObjets = []
        self.dict_angle_distance = {}
        while dataCount < self.nbDonneesACollecter :
            x = self.ser.read().hex()
            if x == "aa":
                if not data_start:
                    data_start = True
            if data_start :
                data.append(x)
                #self.data_dec.append(int(x,16))
                if len(data) > 3 : 
                    LSN = int(data[3],16)*2
                    if len(data) >= LSN + 10:
                        CT = data[2]
                        angle = str(data[5]) + str(data[4])
                        AngleFSA = (int(angle,16)>>1)/64
                        #print(bit_angle)
                        angle = str(data[7]) + str(data[6])
                        AngleLSA = (int(angle,16)>>1)/64
                        diff_angle = AngleLSA - AngleFSA
                        if  0 >= diff_angle  :
                            diff_angle = diff_angle + 360
                        if CT != 1 and LSN != 2:
                            for i in range(10,LSN+10, 2 ):
                                distance = int(str(data[i+1]) + str(data[i]),16)/4
                                if distance != 0 :
                                    angle_correct = math.atan(21.8*((155.3-distance)/(155.3*distance)))
                                else :
                                    angle_correct = 0 
                                angle =   round(((diff_angle / ((LSN/2)-1)) * ((i/2)-3)+ AngleFSA ) + angle_correct,4)
                                angle -= self.correctionAngle0
                                if angle >= 360:
                                    angle -= 360
                                if angle >= 360:
                                    angle -= 360
                                if angle < 0:
                                    angle += 360
                                if distance > 100 : # mm, exclusion des données pour lesquelles la distance est trop faible
                                    dataCount = dataCount +1
                                    try :  # construction de self.dict_angle_distance, assemblage par paquets
                                        list_angle_distance = self.dict_angle_distance[int(angle*2)]
                                        list_angle_distance.append(int(distance))
                                        self.dict_angle_distance[int(angle*2)] = list_angle_distance
                                    except:
                                        self.dict_angle_distance[int(angle*2)] = [int(distance)]
                                    # construction de outputDatList : ajout de la donnée à la liste
                                    self.outputDataList.append([angle,int(distance)]) 
                        data = []
                        data_start = False
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> {dataCount} raw data collected")
        self.stopLidar()
        self.ser.close()

    def stopLidar(self):
        self.ser.write(b'\0xA5\0x65')

    def createOutputDataList(self):

        self.outputDataList=np.asarray(self.outputDataList) # convertit la liste en numpy

        # crée le fichier lidar.csv des données classées par valeurs d'angles égales à 0,5° près
        list_angle = list(self.dict_angle_distance.keys())
        list_angle.sort()
        with open("lidar.csv",'w') as f:
            for key in list_angle:
                f.write("%s,%s\n"%(key,self.dict_angle_distance[key]))

        # Début de la filtration des données et de la détection d'objets        
        self.outputDataList = self.outputDataList[self.outputDataList[:,0].argsort()] # classe toutes les lignes par première colonne

        listScores = self.CalculScores()
        self.outputDataList = np.concatenate((self.outputDataList,listScores),axis=1)
        # exclut les données avec scoreAvant et score Arriere <=1 (donc conserve ScoreAv+ScoreAr>1) et recalcule les scores
        self.outputDataList = self.outputDataList[self.outputDataList[:,2]+self.outputDataList[:,3]>1 ]
        self.outputDataList = self.outputDataList[:,0:2] # efface les colonnes scoreAvant et scoreArrière pour les recalculer sur les données filtrées
        listScores = self.CalculScores() 
        self.outputDataList = np.concatenate((self.outputDataList,listScores),axis=1)
        # calcule scoreDébutObjet et scoreFinObjet (sans la condition sur le max effectuée plus loin)
        listScores2 = listScores[1:,:] # décale d'une ligne en supprimant la première
        listScores3 = listScores[:-1,:] # supprime la dernière ligne
        listScore4 = (listScores2[:,0]-listScores2[:,1])-(listScores3[:,0]-listScores3[:,1])
        scoreDebutObjet = np.insert(listScore4,0,0).reshape(-1,1) # ajoute la première donnée (fixée à 0) pour revenir à la taille de self.outputDataList
        scoreFinObjet = np.insert(listScore4,-1,0).reshape(-1,1) # ajoute la denière donnée (fixée à 0) pour revenir à la taille de self.outputDataList
        self.outputDataList = np.concatenate((self.outputDataList,scoreDebutObjet),axis=1)
        self.outputDataList = np.concatenate((self.outputDataList,scoreFinObjet),axis=1)
        # condition sur le max
        listDebutObjetTemp = np.zeros(scoreDebutObjet.shape) # dimensionne une liste temporaire dont les valeurs sont 0
        listDebutObjet = np.copy(listDebutObjetTemp)
        listFinObjetTemp = np.zeros(scoreFinObjet.shape)
        listFinObjet = np.copy(listFinObjetTemp)
        for i in range(1,5):
            listDebutObjetTemp[scoreDebutObjet > np.roll(scoreDebutObjet,-i)] = 1
            listDebutObjet = listDebutObjet + listDebutObjetTemp
            listDebutObjetTemp[listDebutObjetTemp != 1000] =0 # force toutes les valeurs différentes de 1000 à zéro = efface la liste (aucune valeur ne peut être égale à 1000)
            listFinObjetTemp[scoreFinObjet > np.roll(scoreFinObjet,i)] = 1
            listFinObjet = listFinObjet + listFinObjetTemp
            listFinObjetTemp[listFinObjetTemp != 1000] =0 # force toutes les valeurs différentes de 1.000 à zéro
        listDebutObjet[listDebutObjet < 4]=0
        listDebutObjet[listDebutObjet == 4]=1
        listDebutObjet[self.outputDataList[:,4] < self.seuilEcart] = 0 # condition sur le Seuil : met à 0 tous les scores < SeuilEcart
        listFinObjet[listFinObjet < 4]=0
        listFinObjet[listFinObjet == 4]=1
        listFinObjet[self.outputDataList[:,5] < self.seuilEcart] = 0 # condition sur le Seuil, idem
        self.outputDataList = np.concatenate((self.outputDataList,listDebutObjet),axis=1)
        self.outputDataList = np.concatenate((self.outputDataList,listFinObjet),axis=1)

        # Crée la table des objets
        nbObjets = 0
        flagObjet = False
        for i, listData in enumerate(self.outputDataList):
            if not flagObjet:
                if listData[6] == 1: # Début objet détecté
                    flagObjet = True
                    nbObjets += 1
                    self.listObjets.append([nbObjets, listData[0], listData[1]])
            else:
                if listData[7] == 1: # Fin de l'objet
                   self.listObjets[-1] = self.listObjets[-1] + [listData[0], listData[1]]
                   flagObjet = False
        # dernier objet (si True (objet en cours), termine avec la dernière donnée
        if flagObjet == True:
            self.listObjets[-1] = self.listObjets[-1] + [listData[0], listData[1]]

        np.set_printoptions(suppress=True) # supprime la notation scientifique
        # print(self.outputDataList)
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> {nbObjets} objects detected")

        # print(self.listObjets)

        #print("Numéro de fichier pour sauvegarde ?")
        #numeroDeFichier = input()

        # crée le fichier lidar2.csv des données brutes (taille 7.200 x 2)
        nomDuFichier = "Log/outputLidarFile" + str(self.numeroDeFichier) + ".csv"
        np.savetxt(nomDuFichier, self.outputDataList, fmt= '%.2f', delimiter=",")

        # crée le fichier des objets LidarObjects.csv
        nomDuFichier = "Log/outputObjectsFile" + str(self.numeroDeFichier) + ".csv"
        self.listObjets = np.asarray(self.listObjets) # convertit la liste en numpy
        np.savetxt(nomDuFichier, self.listObjets, fmt= '%.2f', delimiter=",")
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> Data collect completed and files created")
        
    def scan(self):
            self.getData()
            self.createOutputDataList()


if __name__ == "__main__":
    lidar = Lidar()
    lidar.getData()
    lidar.createOutputDataList()
