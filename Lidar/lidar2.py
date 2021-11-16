import serial
import math
import csv
import numpy as np
import matplotlib.pyplot as plt


ser = serial.Serial(port='/dev/ttyUSB0', baudrate='115200')
data_start = False
data = []
data_dec = []
count = 0 # compteur de données collectées (angle, distance)
dict_angle_distance = {} # dictionnaire angles et distances classés par paquets angulaire d'amplitude 0,5° : dimension 720 lignes
outputDataList = [] # liste de données collectées sans classement par paquet : dimension 7.200 lignes
# [angle (degrés), distance (mm), scoreAvant (0 à 5), scoreArrière (0 à 5), scoreDébut objet (-10 à 10), scoreFin objet (-10 à 10), dDébutObjet (0/1), finObjet (0/1)]

nbDonneesACollecter = 7200
filtreEcartDistance = 100 #mm, écart de distance nécessaire pour changer d'objet
seuilEcart = 6 # score de discontinuité à atteindre pour détecter un objet (début ou fin), cf. document protocole

# fonction de calcul des scores Avant et Arrière, cf. doc protocole Lidar
def CalculScores(outputDataList):
    listScores=[]
    for i, dataAngleDistance in enumerate(outputDataList):
        scoreAvant = 0
        scoreArriere = 0
        if i>=len(outputDataList)-1 - 5:
            scoreAvant=5
        else:
            for j in range(1,6):
                if abs(dataAngleDistance[1]-outputDataList[i+j][1])<filtreEcartDistance :
                    scoreAvant += 1
        if i<=4:
            scoreArriere = 5
        else:
            for j in range(1,6):
                if abs(dataAngleDistance[1]-outputDataList[i-j][1])<filtreEcartDistance:
                    scoreArriere += 1
        listScores.append([scoreAvant,scoreArriere])
    listScores=np.asarray(listScores)
    return listScores

# Début de la collecte des données Lidar
while count < nbDonneesACollecter :
    x = ser.read().hex()
    if x == "aa":
        if not data_start:
            data_start = True
    if data_start :
        data.append(x)
        data_dec.append(int(x,16))
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
                #print("PH",data[0:2])
                #print("CT",CT)
                #print("LSN",LSN/2)
                #print("AngleFSA",AngleFSA)
                #print("AngleLSA",AngleLSA)
                #print("CS", data[8:10])
                #print("diff_angle",diff_angle)
                if CT != 1 and LSN != 2:
                    for i in range(10,LSN+10, 2 ):
                        distance = int(str(data[i+1]) + str(data[i]),16)/4
                        if distance != 0 :
                            angle_correct = math.atan(21.8*((155.3-distance)/(155.3*distance)))
                        else :
                            angle_correct = 0 
                        angle =   round(((diff_angle / ((LSN/2)-1)) * ((i/2)-3)+ AngleFSA ) + angle_correct,4)
                        if angle >= 360:
                            angle -= 360
                        if angle >= 360:
                            angle -= 360
                        if distance > 100 : # mm, exclusion des données pour lesquelles la distance est trop faible
                            count = count +1
                            try :  # construction de dict_angle_distance, assemblage par paquets
                                list_angle_distance = dict_angle_distance[int(angle*2)]
                                list_angle_distance.append(int(distance))
                                dict_angle_distance[int(angle*2)] = list_angle_distance
                            except:
                                dict_angle_distance[int(angle*2)] = [int(distance)]
                            # construction de outputDatList : ajout de la donnée à la liste
                            outputDataList.append([angle,int(distance)]) 
                data = []
                data_start = False
                
# fin de la collecte des données, arrêt du Lidar
print (count, " raw data collected")
#ser.write(b'\0xA5\0x65')

outputDataList=np.asarray(outputDataList) # convertit la liste en numpy
#print("(dict_angle_distance",dict_angle_distance)
# crée le fichier lidar.csv des données classées par valeurs d'angles égales à 0,5° près
list_angle = list(dict_angle_distance.keys())
list_angle.sort()
with open("lidar.csv",'w') as f:
    for key in list_angle:
        f.write("%s,%s\n"%(key,dict_angle_distance[key]))

# Début de la filtration des données et de la détection d'objets        
outputDataList = outputDataList[outputDataList[:,0].argsort()] # classe toutes les lignes par première colonne

listScores = CalculScores(outputDataList)
outputDataList = np.concatenate((outputDataList,listScores),axis=1)
# exclut les données avec scoreAvant et score Arriere <=1 (donc conserve ScoreAv+ScoreAr>1) et recalcule les scores
outputDataList = outputDataList[outputDataList[:,2]+outputDataList[:,3]>1 ]
outputDataList = outputDataList[:,0:2] # efface les colonnes scoreAvant et scoreArrière pour les recalculer sur les données filtrées
listScores = CalculScores(outputDataList) 
outputDataList = np.concatenate((outputDataList,listScores),axis=1)
# calcule scoreDébutObjet et scoreFinObjet (sans la condition sur le max effectuée plus loin)
listScores2 = listScores[1:,:] # décale d'une ligne en supprimant la première
listScores3 = listScores[:-1,:] # supprime la dernière ligne
listScore4 = (listScores2[:,0]-listScores2[:,1])-(listScores3[:,0]-listScores3[:,1])
scoreDebutObjet = np.insert(listScore4,0,0).reshape(-1,1) # ajoute la première donnée (fixée à 0) pour revenir à la taille de outputDataList
scoreFinObjet = np.insert(listScore4,-1,0).reshape(-1,1) # ajoute la denière donnée (fixée à 0) pour revenir à la taille de outputDataList
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
listDebutObjet[outputDataList[:,4] < seuilEcart] = 0 # condition sur le Seuil : met à 0 tous les scores < SeuilEcart
listFinObjet[listFinObjet < 4]=0
listFinObjet[listFinObjet == 4]=1
listFinObjet[outputDataList[:,5] < seuilEcart] = 0 # condition sur le Seuil, idem
outputDataList = np.concatenate((outputDataList,listDebutObjet),axis=1)
outputDataList = np.concatenate((outputDataList,listFinObjet),axis=1)

# Crée la table des objets
# [index, angle départ, distance départ, angle fin, distance fin]
listObjets = []
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
# print(outputDataList)
print(nbObjets, " objects detected")
# print(listObjets)

print("Numéro de fichier pour sauvegarde ?")
numeroDeFichier = input()

# crée le fichier lidar2.csv des données brutes (taille 7.200 x 2)
nomDuFichier = "outputLidarFile" + numeroDeFichier + ".csv"
np.savetxt(nomDuFichier, outputDataList, fmt= '%.2f', delimiter=",")

# crée le fichier des objets LidarObjects.csv
nomDuFichier = "outputObjectsFile" + numeroDeFichier + ".csv"
listObjets = np.asarray(listObjets) # convertit la liste en numpy
np.savetxt(nomDuFichier, listObjets, fmt= '%.2f', delimiter=",")

print("Data collect completed and files created")

exit(0)

