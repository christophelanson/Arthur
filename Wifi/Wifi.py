from Mqtt import Mqtt
from Wifi import MqttNetwork
from Json import Json
from colorama import Fore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Wifi(QRunnable):

    def __init__(self):

        super(Wifi, self).__init__()
        self.hardwareName = "wifi"
        self.jsonHandler = Json.JsonHandler()
        self.robotID = self.jsonHandler.read("robotID.json")["ID"]["name"]
        self.listChannel = ["all"]
        self.mqtt = Mqtt.Mqtt(hardwareName=self.hardwareName, on_message=self.on_message, listChannel=self.listChannel)
        self.mqttNetwork = MqttNetwork.MqttNetwork(robotID=self.robotID, on_message=self.on_messageNetwork)

    def on_message(self, client, data, message):
        self.mqtt.decodeMessage(message=message)
        print(self.mqtt.lastCommand,self.mqtt.lastPayload)
        if self.mqtt.lastCommand == "command":
            print(f"Command received from {self.mqtt.lastSender}")

    def on_messageNetwork(self, client, data, message):
        self.mqtt.decodeMessage(message=message)

        if self.mqtt.lastCommand == "send":
            print(f"Command received from {self.mqttNetwork.lastSender}")
            self.write(self.mqtt.lastPayload)
    
    def write(self, data):
        print(f"{Fore.GREEN}INFO (wifi) -> Start sending the payload {data} to {list(self.dictAddress.keys())}")
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

    @pyqtSlot()
    def run(self):
        print("Thread", self.hardwareName, "is running")
