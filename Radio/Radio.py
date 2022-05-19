from circuitpython_nrf24l01.rf24 import RF24
import board
import digitalio
import copy
import RPi.GPIO as GPIO
from colorama import Fore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Mqtt import Mqtt


GPIO.setmode(GPIO.BCM)

class Radio(QRunnable):

    def __init__(self):
        super(Radio, self).__init__()

        node = 1

        self.hardwareName = "radio"
        self.dictAddress = self.setIdentity(node)

        self.initSpi()
        self.initRadio()
        self.nrf.print_details()
        self.nrf.print_pipes()
        self.isCommand = False
        self.isWaiting = False
        self.command = []
        self.state = "listening"
        self.isWriting = False
        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "send":
            self.write(self.mqtt.lastPayload)

    @pyqtSlot()
    def run(self):
        print(f"{Fore.GREEN}INFO -> Radio running with node id", self.node)
                
    def get(self,command):
        if command == "state":
            return self.state 
        return None 
                    
    def setIdentity(self, node):
        self.node = node
        self.dictAllAddress = {1:b"1Node", 2:b"2Node"}
        dictAddressTx = copy.deepcopy(self.dictAllAddress)
        dictAddressTx.pop(node)
        self.ownAddress = self.dictAllAddress[node]
        print(f'{Fore.GREEN}INFO (radio) -> Own = {self.ownAddress}') 
        print(f"{Fore.GREEN}INFO (radio) -> DictAddressTx: {dictAddressTx}")
        return dictAddressTx
    
    def initRadio(self):
        self.nrf.open_tx_pipe(b"NODE1")

        self.nrf.open_rx_pipe(1, b"NODE2") # comprendre pipe / adresse
        #self.nrf.open_rx_pipe(2, b"NODE3") # comprendre pipe / adresse

        #for node in self.dictAddress.keys():
        #self.nrf.open_rx_pipe(1, b"TEST2") # comprendre pipe / adresse
        self.nrf.interrupt_config(data_sent=False, data_fail=False)
        self.nrf.listen = True
        self.nrf.update()
        print(f"{Fore.GREEN}INFO (radio) -> Radio ready for receiving...")
        
    def initSpi(self):
        ce = digitalio.DigitalInOut(board.D4)
        csn = digitalio.DigitalInOut(board.D5)
        spi = board.SPI()  # init spi bus object
        self.nrf = RF24(spi, csn, ce)
        self.nrf.pa_level = -12
        self.radioIrqPin = 12
        self.nrf.channel = 100

        GPIO.setup(self.radioIrqPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.radioIrqPin, GPIO.FALLING, callback=self.read)
        
    def read(self, event):
        print("Received", self.nrf.any(), "on pipe", self.nrf.pipe, ":")
        message = self.nrf.read().decode()
        self.nrf.update()
        print(message)
        
        hardware = message.split("_",1)[0]
        messageToHardware = message.split("_",1)[1]
        print(f"{Fore.GREEN}INFO (radio) -> hardware receiver: {hardware}")
        print(f"{Fore.GREEN}INFO (radio) -> message to hardware: {messageToHardware}")
        self.mqtt.sendMessage(message=messageToHardware, receiver=hardware)
        #self.initSpi()
        #self.initRadio()
            #messageReceived = self.nrf.read().split("/")
            #receiverId = messageReceived[0]
            #receiver = self.hardwareHandler.hardwareDictId[receiverId]
            #self.mqtt.sendMessage(message="/".join(messageReceived[1:]), receiver=receiver)

    def write(self, data):
        print(f"{Fore.GREEN}INFO (radio) -> Start sending the payload {data} to {list(self.dictAddress.keys())}")
        self.nrf.listen = False
        #self.nrf.open_tx_pipe(b"NODE1")
        payload = data.encode("ascii")
        report = self.nrf.send(buf=payload, ask_no_ack=False, force_retry=10, send_only=False)
        if report:
            print(f"{Fore.GREEN}INFO -> Transmission  successfull! ")
        else:
            print(f"{Fore.GREEN}INFO -> Transmission failed or timed out")
        
        #
        # self.nrf.open_rx_pipe(1, b"NODE2") 
        #self.initSpi()
        #self.initRadio()
        self.nrf.listen = True
        self.nrf.update()
        self.state = "listening"
        return

if __name__ == "__main__":
    
    RadioRobot1 = Radio()
    RadioRobot1.write("bonjour")
    #RadioRobot1.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    #while True:
     #   RadioRobot1.read()
# RadioRobot1 = RadioRobot(1)
# while True:
#      RadioRobot1.readAll()

#RadioRobot2 = RadioRobot(2)
#while True:
#    RadioRobot2.writeAll("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


