from Mqtt import Mqtt
from Wifi import MqttNetwork
from Json import Json
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Wifi(QRunnable):

    def __init__(self):

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
        print(self.mqtt.lastCommand,self.mqtt.lastPayload)
        if self.mqtt.lastCommand == "command":
            print(f"Command received from {self.mqttNetwork.lastSender}")
