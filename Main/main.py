import sys
sys.path.insert(0, '../UI')
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')
sys.path.insert(0, '../Lidar')
sys.path.insert(0, '../Camera')

import UI
import Motor
import RadioCommunication
import Lidar
import Camera

import threading
import queue
import time




class ManagerProcess:

    def __init__(self):
        print("start Manager")
        self.communication = RadioCommunication.RadioCommunication(1)
        self.motor = Motor.Motor()
        self.camera = Camera.Camera()
        self.isLidar = False
        try:
            self.lidar = Lidar.Lidar()
            self.isLidar = True
        except Exception as e:
            
            print(e)
        if self.isLidar:
            self.UI = UI.UI(self.motor, self.communication, self.lidar, self.camera)
        else:
            self.UI = UI.UI(self.motor, self.communication, None, self.camera)
        self.communication.setUI(self.UI)

    def run(self):
        print("Start run Thread function")
        threadCommunication = threading.Thread(name='communication', target=self.communication.run)
        threadCommunication.setDaemon(True)
        print("Communication thread start")
        threadmotor = threading.Thread(name='motor', target=self.motor.runProcess)
        threadmotor.setDaemon(True)
        print("Motor thread start")
        
        threadcamera = threading.Thread(name='camera', target=self.camera.run)
        threadcamera.setDaemon(True)
        
        if self.isLidar:
            threadlidar = threading.Thread(name='lidar', target=self.lidar.run)
            threadlidar.setDaemon(True)
        
        self.UI.setThreadId(threadCommunication, threadmotor)
        threadingUI = threading.Thread(name='UI', target=self.UI.runTK)
        threadingUI.setDaemon(True)
        print("UI thread start")
        
        if self.isLidar:
            threadlidar.start()
        threadingUI.start()
        threadCommunication.start()
        threadmotor.start()
        threadcamera.start()
        
        threadmotor.join()
        threadCommunication.join()
        threadcamera.join()
        if self.isLidar:
            threadlidar.join()
        threadingUI.join()
        

if __name__ == "__main__":
    managerProcess = ManagerProcess()
    managerProcess.run()
