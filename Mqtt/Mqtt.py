import paho.mqtt.client as mqtt

class Mqtt:

    def __init__(self,hardwareName,on_message, listChannel):
        self.client = mqtt.Client(hardwareName)
        self.client.on_message=on_message
        self.client.connect('localhost', port=9999)
        for channel in listChannel:
            self.client.subscribe(channel)
        self.client.loop_start()