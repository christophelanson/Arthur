import paho.mqtt.client as mqtt
from Json import Json
import os
import sys
sys.path.append(".")

class Mqtt:

    def __init__(self, hardwareName,on_message, listChannel):
        self.hardwareName = hardwareName
        self.client = mqtt.Client(client_id=self.hardwareName)
        self.client.on_message=on_message
        self.client.connect('localhost', port=1883)
        self.lastTopic = ""
        self.lastSender = ""
        self.lastMessage = ""
        self.lastPayload = ""
        self.lastCommand = ""
        self.waitingAwnser = False

        for channel in listChannel:
            self.client.subscribe(channel)

        self.json = Json.JsonHandler()

        hardwareList = self.json.read("Main/idRobot.json")["modules"]

        for hardware in hardwareList:
            if hardware != self.hardwareName:
                channel = hardware+"/"+self.hardwareName
                self.client.subscribe(channel)
                print(self.hardwareName, "subscribe to", channel)

        self.client.loop_start()
    
    def decodeMessage(self, message):
        self.lastMessage = str(message.payload.decode())
        self.lastCommand = self.lastMessage.split("/")[0]
        self.lastPayload = self.lastMessage.split("/")[1]
        self.lastTopic = message.topic
        self.lastSender = self.lastTopic.split("/")[0]
        print(self.hardwareName, "recevied message from:", self.lastSender, ":")
        print("\r message: ", self.lastMessage)
        self.waitingAwnser = False
    
    def sendMessage(self, message, receiver, awnserNeeded = False):
        topic = self.hardwareName + "/" + receiver
        self.client.publish(topic, message)
        print(self.hardwareName, "send", message,"to", receiver)
        if awnserNeeded:
            self.waitingAwnser = True
            while self.waitingAwnser:
                pass
            return self.lastPayload
