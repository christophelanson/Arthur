import sys
sys.path.insert(0, '../UI')
sys.path.insert(0, '../Communication')
sys.path.insert(0, '../Motor')

import UI
import Motor
import RadioCommunication

import threading
import queue
import time




class ManagerProcess:

    def __init__(self):
        print("start Manager")
        self.communication = RadioCommunication.RadioCommunication(1)
        self.motor = Motor.Motor()
        self.UI = UI.UI(self.motor, self.communication)
        self.communication.setUI(self.UI)

    def run(self):
        print("Start run Thread function")
        threadCommunication = threading.Thread(name='communication', target=self.communication.run)
        threadCommunication.setDaemon(True)
        print("Communication thread start")
        threadmotor = threading.Thread(name='motor', target=self.motor.runProcess)
        threadmotor.setDaemon(True)
        print("Motor thread start")
        
        self.UI.setThreadId(threadCommunication, threadmotor)
        threadingUI = threading.Thread(name='UI', target=self.UI.runTK)
        threadingUI.setDaemon(True)
        print("UI thread start")
        
        threadingUI.start()
        threadCommunication.start()
        threadmotor.start()
        threadmotor.join()
        threadCommunication.join()
        threadingUI.join()


if __name__ == "__main__":
    managerProcess = ManagerProcess()
    managerProcess.run()
