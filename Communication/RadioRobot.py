# message structure:
# [0] : command
# [1:] : payload

from circuitpython_nrf24l01.rf24 import RF24
import board
import digitalio
import copy
import struct
import time
import RPi.GPIO as GPIO
from colorama import Fore
import sys
from Message.MessageRouter import MessageRouter


GPIO.setmode(GPIO.BCM)


class RadioRobot:

    def __init__(self, node, messageRouter:MessageRouter, hardwareId):
        
        self.hardwareName = "radio"
        self.hardwareId = hardwareId
        self.messageRouter = messageRouter
        self.dictAddress = self.setIdentity(node)

        self.initSpi()
        self.initRadio()
        self.isCommand = False
        self.isWaiting = False
        self.command = []
        self.state = "listening"
        self.isWriting = False
        
    def runPara(self):
        
        while True:
            if self.isCommand:
                if self.command[0] == self.messageRouter.dictCommand["SEND"]:
                    self.state = "writing"
                    self.isWriting = True
                    payload = self.command[1:]
                    self.write(payload)
                self.isCommand = False
                
    def get(self,command):
        if command == "state":
            return self.state
        
       # if self.command[0] == MessageRouter.dictCommand["Send"]:
        #        payload = command[1:]
         #       self.write(payload)
          #      while True:
                    
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
        for node in self.dictAddress.keys():
            self.nrf.open_rx_pipe(1, self.dictAddress[node]) # comprendre pipe / adresse
        self.nrf.open_tx_pipe(self.ownAddress)
        self.nrf.listen = True
        print(f"{Fore.GREEN}INFO (radio) -> Radio ready for receiving...")
        
    def initSpi(self):
        ce = digitalio.DigitalInOut(board.D4)
        csn = digitalio.DigitalInOut(board.D5)
        spi = board.SPI()  # init spi bus object
        self.nrf = RF24(spi, csn, ce)
        self.nrf.pa_level = -12
        self.radioIrqPin = 12
        GPIO.setup(self.radioIrqPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.radioIrqPin, GPIO.FALLING, callback=self.read)
        

    def read(self, event):
        if not self.isWriting:
            print("Received", self.nrf.any(), "on pipe", self.nrf.pipe, ":")
            messageReceived = self.nrf.read()
            self.messageRouter.unroute(messageReceived, 'radio')
            
#             payload = string(messageRadio[2:])
#             hardwareName = payload[0]
#             command = payload[1]
#             payload = payload[2:]
#             if receiver == self.node:
#                 if isGet and sender != self.node :
#                     result = self.messageRouter.route(self.node, hardwareName, command, isGet)
#                     self.messageRouter.route(sender, 'radio', result, isSet)
#                 else:
#                     self.messageRouter.route(self.node, hardwareName, command)

    def write(self, data):
        print(f"{Fore.GREEN}INFO (radio) -> Start sending the payload {data} to {list(self.dictAddress.keys())}")
        #self.initSpi()
        #self.openListenChanel(self.dictAddress)
        #self.openSpeakChanel()
        #self.nrf.clear_status_flags()
        self.nrf.listen = False
        payload = data.encode("ascii")
        report = self.nrf.send(buf=payload, ask_no_ack=False, force_retry=100, send_only=False)
        if report:
            print(f"{Fore.GREEN}INFO -> Transmission  successfull! ")
        else:
            print(f"{Fore.GREEN}INFO -> Transmission failed or timed out")
            #self.messageRouter.unroute(messageReceived, 'radio')
        self.nrf.listen = True
        self.state = "listening"
        self.isWriting = False
        return

if __name__ == "__main__":
    
    RadioRobot1 = RadioRobot(1)
    RadioRobot1.runPara()
    #RadioRobot1.write("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    #while True:
     #   RadioRobot1.read()
# RadioRobot1 = RadioRobot(1)
# while True:
#      RadioRobot1.readAll()

#RadioRobot2 = RadioRobot(2)
#while True:
#    RadioRobot2.writeAll("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


