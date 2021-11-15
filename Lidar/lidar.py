import serial
import math
import csv
import numpy as np
import matplotlib.pyplot as plt

ser = serial.Serial(port='/dev/ttyUSB0', baudrate='115200')
data_start = False
data = []
data_dec = []
count = 0
dict_angle_distance = {}

while 1 :
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
    #             print("starting bytes",data[0:2])
    #             print("packet types",data[2])
                #print("number of samples",data[3], int(data[3],16))
    #             print("starting angles",data[4:6])
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
                        angle =   round(((diff_angle / ((LSN/2)-1)) * ((i/2)-3)+ AngleFSA ) + angle_correct,2)
                        if angle >= 360:
                            angle -= 360
                        #print("angle:", angle,"distance:" , distance, "LSB:",data[i], "MSB:", data[i+1])
                        if distance > 100 : # mm
                            count = count +1
                            try :
                                list_angle_distance = dict_angle_distance[int(angle*2)]
                                list_angle_distance.append(int(distance))
                                dict_angle_distance[int(angle*2)] = list_angle_distance
                            except:
                                dict_angle_distance[int(angle*2)] = [int(distance)]
                data = []
                data_start = False
                if count > 7200:
                    print("(dict_angle_distance",dict_angle_distance)
                    list_angle = list(dict_angle_distance.keys())
                    list_angle.sort()
                    with open("lidar.csv",'w') as f:
                        for key in list_angle:
                            f.write("%s,%s\n"%(key,dict_angle_distance[key]))
                    
                    list_angle = list(dict_angle_distance.keys())
                    for i in range(len(list_angle)-1):
                        list_angle[i] = (list_angle[i] * 3.14159)/180
        
                    
                    list_temp =[]
                    list_distance = list(dict_angle_distance.values())
                    for i in list_distance:
                        list_temp.append(np.mean(i))
                    print("list_angle",list_angle)
                    print("list_temp",list_temp)
                    plt.figure()
                    plt.polar(list_angle, list_temp,'o')
                    
                    plt.show()
                    exit(0)
        
