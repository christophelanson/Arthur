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
    return roboticArmAngle, roboticArmDistance


print(lidar_to_roboticArm_conversion(65,1000))
