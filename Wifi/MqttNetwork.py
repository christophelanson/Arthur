import paho.mqtt.client as mqtt
import sys
from colorama import Fore
sys.path.append(".")
from Json import Json


class MqttNetwork:

    def __init__(self, robotID, on_message):

        self.jsonHandler = Json.JsonHandler()
        self.robotID = robotID
        self.client = mqtt.Client(client_id=self.robotID)
        self.client.on_message=on_message
        self.client.connect('10.0.0.1')
        self.lastTopic = ""
        self.lastSender = ""
        self.lastMessage = ""
        self.lastPayload = ""
        self.lastCommand = ""
        self.dictWaitingAwnser = {}

        environmentRobots = self.jsonHandler.read("robotID.json")["environment"]["robotNames"]

        for robot in environmentRobots:
            if robot != self.robotID:
                channel = robot+"/"+self.robotID
                self.client.subscribe(channel)
                print(f"{Fore.GREEN}INFO (MQTT/{self.robotID}) -> {self.robotID} subscribed to {channel}")
                
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
        topic = self.robotID + "/" + receiver
        self.client.publish(topic, message)
        #print(self.hardwareName, "send", message,"to", topic)
        if awnserNeeded:
            responseTopic = receiver + "/" + self.robotID 
            #print("waiting for", responseTopic )
            self.dictWaitingAwnser[responseTopic] = True
            while self.dictWaitingAwnser[responseTopic]:
                pass
            return self.lastPayload
