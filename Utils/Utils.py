import json
from math import cos, sin, sqrt, atan, acos, pi

#-------------------
# JSON import and conventions
#-------------------

# loading from robotID.json
with open('robotID.json') as jsonFile:
    robotID = json.load(jsonFile)

#-------------------
# FUNCTIONS
#-------------------

def lidar_to_roboticArm_conversion(lidarAngle,lidarDistance):
    """
    from an (angle,distance) measured by the lidar
    returns the corresponding (angle,distance) for the robotic arm

    nota : angles are measured clockwise from robot North
    angles input in degrees, distances in mm
    """
    try:
        lidarPosition = robotID['lidar']['position']
        roboticArmPosition = robotID['roboticArm']['SPosition']
    except Exception as e:
        print(e,"lidar or roboticArm json data unfound")

    lidarAngle = lidarAngle * pi/180 # to radians
    # calculate lidar roboticArm angle, distance
    lidarRoboticArmDistance = sqrt((lidarPosition[0]-roboticArmPosition[0])**2+(lidarPosition[1]-roboticArmPosition[1])**2)
    lidarRoboticArmAngle = atan((lidarPosition[0]-roboticArmPosition[0])/(lidarPosition[1]-roboticArmPosition[1]))
    # calculate outputs
    roboticArmDistance = sqrt(lidarDistance**2+lidarRoboticArmDistance**2-2*lidarDistance*lidarRoboticArmDistance*cos(lidarAngle-lidarRoboticArmAngle))
    roboticArmAngle = acos((lidarDistance**2-lidarRoboticArmDistance**2-roboticArmDistance**2)/2/lidarRoboticArmDistance/roboticArmDistance)+lidarRoboticArmAngle
    roboticArmAngle = roboticArmAngle * 180/pi
    return round(roboticArmAngle,2), round(roboticArmDistance)

def motor_distance_to_time(distance,initSpeed,maxSpeed,finalSpeed,smoothRun = True):
    """
    for a given distance in m and a motor speed given as a percentage of (an input 50 means 50% of maxMotorSpeed)
    returns expected time in sec to cover this distance
    
    smoothRun = True: takes acceleration and deceleration ito account
    smoothRun = False : assumes full speed all the way

    NB : maxMotorSpeed in m/s
    """
    dT = robotID['motors']['dT']
    maxMotorSpeed = robotID['motors']['maxSpeed']
    if smoothRun:
        runTime = ((distance/dT-2.5*(initSpeed+finalSpeed)/100)/(maxSpeed/100)+5)*dT/maxMotorSpeed
    else:
        runTime = distance/(maxSpeed/100)/maxMotorSpeed
    return round(runTime,2)

#print(lidar_to_roboticArm_conversion(65,1000))
print(motor_distance_to_time(0.873,0,50,00, smoothRun=True))
print(motor_distance_to_time(0.873,0,100,0, smoothRun=False))