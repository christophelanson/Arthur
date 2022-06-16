import paho.mqtt.client as mqtt
import sys
from colorama import Fore
sys.path.append(".")
from Json import Json


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
        self.dictWaitingAwnser = {}

        for channel in listChannel:
            self.client.subscribe(channel)
            self.dictWaitingAwnser[channel] = False

        self.json = Json.JsonHandler()

        hardwareList = self.json.read("robotID.json")["ID"]["hardwareList"]

        for hardware in hardwareList:
            if hardware != self.hardwareName:
                channel = hardware+"/"+self.hardwareName
                self.client.subscribe(channel)
                print(f"{Fore.GREEN}INFO (MQTT/{self.hardwareName}) -> {self.hardwareName} subscribed to {channel}")

                #channel = self.hardwareName+"/"+hardware
                #self.client.subscribe(channel)
                #print(f"{Fore.GREEN}INFO (MQTT/{self.hardwareName}) -> {self.hardwareName} subscribed to {channel}")


        self.client.loop_start()
    
    def decodeMessage(self, message):
        self.lastMessage = str(message.payload.decode())
        self.lastCommand = self.lastMessage.split("/",1)[0]
        self.lastPayload = self.lastMessage.split("/",1)[1]
        self.lastTopic = message.topic
        self.lastSender = self.lastTopic.split("/")[0]
        #print(f"{self.hardwareName} received {self.lastMessage} from: {self.lastSender}")
        #print("\r message: ", self.lastMessage)
        self.dictWaitingAwnser[message.topic] = False
        #print("desactivate", message.topic)
    
    def sendMessage(self, message, receiver, awnserNeeded = False):
        topic = self.hardwareName + "/" + receiver
        self.client.publish(topic, message)
        #print(self.hardwareName, "send", message,"to", topic)
        if awnserNeeded:
            responseTopic = receiver + "/" + self.hardwareName 
            #print("waiting for", responseTopic )
            self.dictWaitingAwnser[responseTopic] = True
            while self.dictWaitingAwnser[responseTopic]:
                pass
            return self.lastPayload
