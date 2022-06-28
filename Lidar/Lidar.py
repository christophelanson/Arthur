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
#from DataBase import DataBase
from colorama import Fore
import random



class Lidar(QRunnable):
    """
    The Lidar process creates several tables/dictionnaries :

    dict_angle_distance = {} # dictionnaire angles et distances classés par paquets angulaire d'amplitude 0,5° : dimension 720 lignes,
        plusieurs données possibles par ligne

    outputDataList = [] # liste de données collectées sans classement par paquet : dimension 7.200 lignes (cf. nbDonnesACollecter)
        [angle (degrés), distance (mm), scoreAvant (0 à 5), scoreArrière (0 à 5), scoreDébut objet (-10 à 10), 
        scoreFin objet (-10 à 10), dDébutObjet (0/1), finObjet (0/1)]

    listObjets = [] # liste des objets [index, angle départ, distance départ, angle fin, distance fin]

    dict_angle_distanc is stored in Log/Lidar.csv (in getData() function, optional storage through flag)
    outputDataList is strored in Log/outputLidarFile.csv, this file is overwritten each time Lidar is run
    listObjets is stored in Log/outputObjectsFile.csv, this file is overwritten each time Lidar is run
        listObjets is also stored il Log/ with a sequencenumber to trace history of Lidar scans
    """

    def __init__(self): #, messageRouter):
        super(Lidar, self).__init__()
        self.hardwareName = "lidar"
        #self.dataBase = DataBase.DataBase(id=self.hardwareName)
        self.ser = serial.Serial(port='/dev/ttyUSB0', baudrate='115200') #/dev/ttyUSB0
        self.ser.close()
        self.nbDonneesACollecter = 7200 # 7200
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
            self.mqtt.sendMessage(message="return/1", receiver=self.mqtt.lastSender)
        
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
            print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> lidar now scanning around")
            outputDataList = self.getData(saveLidarCSV=False)
            self.createOutputDataList(outputDataList)

# fonction de calcul des scores Avant et Arrière, cf. doc protocole Lidar
    def CalculScores(self,outputDataList):
        listScores=[]
        for i, dataAngleDistance in enumerate(outputDataList):
            scoreAvant = 0
            scoreArriere = 0
            if i>=len(outputDataList)-1 - 5:
                scoreAvant=5
            else:
                for j in range(1,6):
                    if abs(dataAngleDistance[1]-outputDataList[i+j][1])<self.filtreEcartDistance :
                        scoreAvant += 1
            if i<=4:
                scoreArriere = 5
            else:
                for j in range(1,6):
                    if abs(dataAngleDistance[1]-outputDataList[i-j][1])<self.filtreEcartDistance:
                        scoreArriere += 1
            listScores.append([scoreAvant,scoreArriere])
        listScores=np.asarray(listScores)
        return listScores
    
    def getData(self,saveLidarCSV=False):
        """
        runs a Lidar scan to collect self.nbDonneesACollecter data
        returns outputDataList tha IS NOT the definite file (see createOutputDtaList function)
        at this stage outputdataList only has 2 columns (angle and distance)
        """
        self.ser.open()
        # Début de la collecte des données Lidar
        dataCount = 0 # compteur de données collectées (angle, distance)
        data = []
        data_start = False
        outputDataList = []
        dict_angle_distance = {}
        while dataCount < self.nbDonneesACollecter :
#            print(dataCount)
            x = self.ser.read().hex()
            if x == "aa":
                if not data_start:
                    data_start = True
            if data_start :
                data.append(x)
                #self.data_dec.append(int(x,16))
                if len(data) > 3 : 
                    LSN = int(data[3],16)*2
#                    print(LSN)                    
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
#                                print(distance)
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
                                        list_angle_distance = dict_angle_distance[int(angle*2)]
                                        list_angle_distance.append(int(distance))
                                        dict_angle_distance[int(angle*2)] = list_angle_distance
                                    except:
                                        dict_angle_distance[int(angle*2)] = [int(distance)]
                                    # construction de outputDatList : ajout de la donnée à la liste
                                    outputDataList.append([angle,int(distance)])
                        data = []
                        data_start = False
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> {dataCount} raw data collected")
        self.stopLidar()
        self.ser.close()

        # crée le fichier lidar.csv des données classées par valeurs d'angles égales à 0,5° près
        if saveLidarCSV == True:
            list_angle = list(dict_angle_distance.keys())
            list_angle.sort()
            with open("Log/lidar.csv",'w') as f:
                for key in list_angle:
                    f.write("%s,%s\n"%(key,dict_angle_distance[key]))

        return outputDataList


    def stopLidar(self):
        self.ser.write(b'\0xA5\0x65')


    def createOutputDataList(self,outputDataList, sequenceNumber=0):
        """
        builds a full outputDataList 
        from a 2 columns (angle, distance) initial data list
        then creates and returns a list of Objetcs

        outputDataList structure :
            [angle (degrés), distance (mm), scoreAvant (0 à 5), scoreArrière (0 à 5), scoreDébut objet (-10 à 10), 
            scoreFin objet (-10 à 10), dDébutObjet (0/1), finObjet (0/1)]
        listObjets structure :
            [index, angle départ, distance départ, angle fin, distance fin]
        """

        listObjets = []
        outputDataList = np.asarray(outputDataList) # convertit la liste en numpy

        # Début de la filtration des données et de la détection d'objets        
        outputDataList = outputDataList[outputDataList[:,0].argsort()] # classe toutes les lignes par première colonne

        listScores = self.CalculScores(outputDataList)
        outputDataList = np.concatenate((outputDataList,listScores),axis=1)
        # exclut les données avec scoreAvant et score Arriere <=1 (donc conserve ScoreAv+ScoreAr>1) et recalcule les scores
        outputDataList = outputDataList[outputDataList[:,2]+outputDataList[:,3]>1 ]
        outputDataList = outputDataList[:,0:2] # efface les colonnes scoreAvant et scoreArrière pour les recalculer sur les données filtrées
        listScores = self.CalculScores(outputDataList) 
        outputDataList = np.concatenate((outputDataList,listScores),axis=1)
        # calcule scoreDébutObjet et scoreFinObjet (sans la condition sur le max effectuée plus loin)
        listScores2 = listScores[1:,:] # décale d'une ligne en supprimant la première
        listScores3 = listScores[:-1,:] # supprime la dernière ligne
        listScores4 = (listScores2[:,0]-listScores2[:,1])-(listScores3[:,0]-listScores3[:,1])
        scoreDebutObjet = np.insert(listScores4,0,0).reshape(-1,1) # ajoute la première donnée (fixée à 0) pour revenir à la taille de self.outputDataList
        scoreFinObjet = np.insert(listScores4,-1,0).reshape(-1,1) # ajoute la denière donnée (fixée à 0) pour revenir à la taille de self.outputDataList
        outputDataList = np.concatenate((outputDataList,scoreDebutObjet),axis=1)
        outputDataList = np.concatenate((outputDataList,scoreFinObjet),axis=1)
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
        listDebutObjet[outputDataList[:,4] < self.seuilEcart] = 0 # condition sur le Seuil : met à 0 tous les scores < SeuilEcart
        listFinObjet[listFinObjet < 4]=0
        listFinObjet[listFinObjet == 4]=1
        listFinObjet[outputDataList[:,5] < self.seuilEcart] = 0 # condition sur le Seuil, idem
        outputDataList = np.concatenate((outputDataList,listDebutObjet),axis=1)
        outputDataList = np.concatenate((outputDataList,listFinObjet),axis=1)

        # Crée la table des objets
        nbObjets = 0
        flagObjet = False
        for i, listData in enumerate(outputDataList):
            if not flagObjet:
                if listData[6] == 1: # Début objet détecté
                    flagObjet = True
                    nbObjets += 1
                    listObjets.append([nbObjets, listData[0], listData[1]])
            else:
                if listData[7] == 1: # Fin de l'objet
                   listObjets[-1] = listObjets[-1] + [listData[0], listData[1]]
                   flagObjet = False
        # dernier objet (si True (objet en cours), termine avec la dernière donnée
        if flagObjet == True:
            listObjets[-1] = listObjets[-1] + [listData[0], listData[1]]

        np.set_printoptions(suppress=True) # supprime la notation scientifique
        # print(self.outputDataList)
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> {nbObjets} objects detected")

        # print(self.listObjets)

        #print("Numéro de fichier pour sauvegarde ?")
        #numeroDeFichier = input()
        numeroDeFichier = sequenceNumber

        # crée le fichier lidar2.csv des données brutes (taille 7.200 x 2)
        # current file (fichier courant)
        nomDuFichier = "Log/outputLidarFile.csv"
        np.savetxt(nomDuFichier, outputDataList, fmt= '%.2f', delimiter=",")

        # crée le fichier des objets LidarObjects.csv
        listObjets = np.asarray(listObjets) # convertit la liste en numpy
        # currentFile (fichier courant)
        nomDuFichier = "Log/outputObjectsFile.csv"
        np.savetxt(nomDuFichier, listObjets, fmt= '%.2f', delimiter=",")
        # fichier à enregistrer avec le numéro de la séquence
        nomDuFichier = "Log/outputObjectsFile" + str(numeroDeFichier) + ".csv"     
#        np.savetxt(nomDuFichier, self.listObjets, fmt= '%.2f', delimiter=",") # log
        print(f"{Fore.GREEN}INFO ({self.hardwareName}) -> Data collect completed and files created")

        return listObjets
        
    def scan(self):
            outputDataList = self.getData()
            self.createOutputDataList(outputDataList)


if __name__ == "__main__":
    lidar = Lidar()
    outputDataList = lidar.getData()
    lidar.createOutputDataList(outputDataList)
