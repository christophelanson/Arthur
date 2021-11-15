import threading
import queue
import time
import UI
import Motor
import Communication


class ManagerProcess:

    def __init__(self):
        print("start Manager")
        self.communication = Communication.RadioCommuncation(1)
        self.motor = Motor.Motor()
        self.UI = UI.UI()

    def run(self):
        threadingUI = threading.Thread(name='listen', target=self.ui.runTK())
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