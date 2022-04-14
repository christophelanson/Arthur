import paho.mqtt.client as mqtt
from Json import Json

class Mqtt:

    def __init__(self,hardwareName,on_message, listChannel):
        self.client = mqtt.Client(client_id=hardwareName)
        self.client.on_message=on_message
        self.client.connect('localhost', port=1883)

        for channel in listChannel:
            self.client.subscribe(channel)

        self.json = Json.json()
        hardwareList = self.json.read()

        for hardware in hardwareList:
            if hardware != hardwareName:
                channel = hardwareName+"/"+hardware
                self.client.subscribe(channel)
                print(hardwareName, "subscribe to", channel)

        self.client.loop_start()