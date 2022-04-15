import smbus
from time import sleep 
from Mqtt import Mqtt
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from DataBase import DataBase


AddressCOMPASS = 0x02
AddressPITCH = 0x04
AddressROLL = 0x05

class Compass(QRunnable):

    def __init__(self):
        super(Compass, self).__init__()
        self.hardwareName = "gyro"
        self.dataBase = DataBase.DataBase(id=self.hardwareName)
        
        self.state = "ready"
        self.bus = smbus.SMBus(1) 
        self.Device_Address = 0x60  
        self.bus.write_byte_data(self.Device_Address, 0, 1)
        self.state = "init"

        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)
        self.speedData = 1
 

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "getSensorValue":
            message = "value/" + self.getSensorValue()
            self.mqtt.sendMessage(message=message, receiver=self.mqtt.lastSender)
        
        if self.mqtt.lastCommand == "setSpeedData":
           self.setSpeedData()

    @pyqtSlot()
    def run(self):
        print("Thread", self.hardwareName, "is running")
        while True:
            sleep(0.1)
            self.sendValue()
        self.timer = QTimer()
        self.timer.timeout.connect(self.sendValue)
        print("Thread", self.hardwareName, "is running")
        self.timer.start(self.speedData)

    def sendValue(self):
        value = self.getSensorValue()
        self.dataBase.updateSensorValue("gyro", value)
        #message = "gyroValue/" + self.getSensorValue()
        #self.mqtt.sendMessage(message=message, receiver="motor")

    def setSpeedData(self):
        self.speedData = self.mqtt.lastPayload
        self.timer.stop()
        self.timer.start(self.speedData)

    def getSensorValue(self):
        compass = self.readRegister16bits(AddressCOMPASS)/10
        pitch = self.readRegister8bits(AddressPITCH)
        roll = self.readRegister8bits(AddressROLL)
        return str(compass)+"-"+str(pitch)+"-"+str(roll)
        
    def readRegister16bits(self, addr):        
            high = self.bus.read_byte_data(self.Device_Address, addr)
            low = self.bus.read_byte_data(self.Device_Address, addr+1)
            value = ((high << 8) | low)
            if(value > 32768):
                    value = value - 65536
            return value
    
    def readRegister8bits(self, addr):        
        return self.bus.read_byte_data(self.Device_Address, addr)
       

if __name__ == "__main__":
    
    compass = Compass(None)
    compass.run()
    