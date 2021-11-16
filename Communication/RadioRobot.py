from circuitpython_nrf24l01.rf24 import RF24
import board
import digitalio
import copy
import struct
import time

class RadioRobot:

    def __init__(self, Name):

        self.dictAllAddress = {1:b"1Node", 2:b"2Node"}
        self.initSpi()
        self.Name = Name
        self.ownAddress = ""
        self.dictAddress = self.setIdentity(Name)
        self.openListenChanel(self.dictAddress)
        self.openSpeakChanel()

    def initSpi(self):
        # change these (digital output) pins accordingly
        ce = digitalio.DigitalInOut(board.D4)
        csn = digitalio.DigitalInOut(board.D5)

        # using board.SPI() automatically selects the MCU's
        # available SPI pins, board.SCK, board.MOSI, board.MISO
        spi = board.SPI()  # init spi bus object

        # we'll be using the dynamic payload size feature (enabled by default)
        # initialize the nRF24L01 on the spi bus object
        self.nrf = RF24(spi, csn, ce)

        # set the Power Amplifier level to -12 dBm since this test example is
        # usually run with nRF24L01 transceivers in close proximity
        self.nrf.pa_level = -12
        

    def setIdentity(self, Name):
            dictAddressTx = copy.deepcopy(self.dictAllAddress)
            dictAddressTx.pop(Name)
            self.ownAddress = self.dictAllAddress[Name]
            print("own", self.ownAddress) 
            print("dictAddressTx",dictAddressTx)
            return dictAddressTx

    def openListenChanel(self, dictAddress):
        for name in dictAddress.keys():
            self.nrf.open_rx_pipe(1, dictAddress[name]) # comprendre pipe / adresse

    def listenChanel(self):
        print("listening..")
        self.initSpi()
        self.nrf.clear_status_flags()
        self.openListenChanel(self.dictAddress)
        self.openSpeakChanel()
        self.nrf.listen = True
        while True:
            if self.nrf.available():  # keep RX FIFO empty for reception
                payload_size, pipe_number = (self.nrf.any(), self.nrf.pipe)
                print("Received", self.nrf.any(), "on pipe", self.nrf.pipe, ":")
                receiveData = self.nrf.read()
                payload = []
                for char in receiveData:
                    payload.append(chr(char))
                self.nrf.listen = False
                return payload

    def openSpeakChanel(self):
        print("open speak chanel start")
        #self.nrf.listen = False
        self.nrf.open_tx_pipe(self.ownAddress)
        print("Channel for writing from:", list(self.ownAddress))
         
    def speakChanel(self, data, dictAddress):
        print("speak chanel")
        self.initSpi()
        self.openListenChanel(self.dictAddress)
        self.openSpeakChanel()
        self.nrf.clear_status_flags()
        self.nrf.listen = False
        count = 1 
        payload = data.encode("ascii")
        report = self.nrf.send(payload)
        if report:
            print("Transmission  successfull! ")
        else:
            print("Transmission failed or timed out")
        while not report:
            report = self.nrf.send(payload)
            if report:
                print("Transmission  successfull! ")
            else:
                print("Transmission failed or timed out")
            count += 1
            if count > 10:
                print("break")
                break

    def read(self, listName):
        dictAddressRead = {}
        for name in listName:
            dictAddressRead[name] = self.dictAddress[name]
        payload = self.listenChanel()
        return payload

    def readAll(self):
        print("start listening")
        payload = self.listenChanel()
        return payload

    def write(self, listName, data):
        dictAddressWrite = {}
        for name in listName:
            dictAddressWrite[name] = self.dictAddress[name]
        self.speakChanel(data,dictAddressWrite)

    def writeAll(self, data):
        print("Start writing")
        dictAddress = self.dictAddress
        self.speakChanel(data,self.dictAddress)


# RadioRobot1 = RadioRobot(1)
# while True:
#      RadioRobot1.readAll()

#RadioRobot2 = RadioRobot(2)
#while True:
#    RadioRobot2.writeAll("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


