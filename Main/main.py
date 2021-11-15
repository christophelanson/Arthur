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
        threadingUI = threading.Thread(name='listen', target=self.UI.runTK())
        threadingUI.setDaemon(True)
        threadCommunication = threading.Thread(name='listen', target=self.communication.listen())
        threadCommunication.setDaemon(True)
        threadmotor = threading.Thread(name='listen', target=self.motor.runProcess())
        threadmotor.setDaemon(True)

        threadingUI.start()
        threadCommunication.start()
        threadmotor.start()
        threadmotor.join()
        threadCommunication.join()
        threadingUI.join()


if __name__ == "__main__":
    try:

        managerProcess = ManagerProcess()
        managerProcess.run()

    except KeyboardInterrupt:
        print("finished")