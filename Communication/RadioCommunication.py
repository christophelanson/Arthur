import RadioRobot
import ExceptionFile

class RadioCommunication:

    def __init__(self, name):

        self.name = name
        self.Radio = RadioRobot.RadioRobot(name)
        self.isIdle = True
        self.isSilent = False
        self.isReceiving = False
        self.isSending = False
        self.isMaster = self.checkMaster()
        self.requestMessage = ["wantToSpeak"]
        self.receivedMessage = []
        self.commandToSend = ""
        self.dictCommande = {"startByte": 0x00,
                             "stopByte": 0x40,
                             "wantToSpeak": 0x10,
                             "PermissionToSpeak": 0x11,
                             "TurnLeft": 0x12,
                             "TurnRigth": 0x13,
                             "RUN": 0x14,
                             "TURN": 0x15,
                             "STOP": 0x16,
                             "SCAN": 0x17,
                             }  # hexa : 0 , 255 , 16 , 17
    
    def setUI(self, UI):
        self.UI = UI
        print("Communication UI set")
        
    def run(self):
        pass

    def checkMaster(self):
        return self.Name == 1

    def readAll(self):
        payload = self.Radio.readAll()
        self.decodeData(payload)
        return payload

    def write(self, listName, data):
        data = self.codeData(data)
        self.Radio.write(listName, data)

    def writeAll(self, data):
        data = self.codeData(data)
        self.Radio.writeAll(data)

    def decodeData(self, data):
        node_id, message = self.convertData(data)
        if self.isMaster and message == self.dictCommande["wantToSpeak"]:
            data = self.codeData([self.dictCommande["PermissionToSpeak"], node_id])
            self.Radio.writeAll(data)

        if not self.isMaster:
            if message[0] == self.dictCommande["PermissionToSpeak"]:
                if message[1] == self.Name:
                    self.asPermissionToSpeak = True
                    self.isSilent = False
                else:
                    self.asPermissionToSpeak = False
                    self.isSilent = True
            else:
                self.executeCmd(message)

    def executeCmd(self, message):
        message = hex(ord(message))

    def convertData(self, data):
        node_id = data[0]
        message = data[2]
        node_id = data[1]
        return node_id, message

    def wantToSpeak(self):
        data = self.codeData(self.dictCommande["wantToSpeak"])
        self.write([0], data)

    def send(self, data):
        if self.isMaster or not self.isMaster:
            self.writeAll(data)
            return True
        else:
            if self.isSilent:
                return False
            if self.isIdle:
                data = self.codeData(data)
                self.wantToSpeak()
                response = self.readAll()
                self.decodeData(response)
                if self.asPermissionToSpeak:
                    self.write([0], data)
                    return True
        return False

    def codeData(self, data):
        payload = chr(self.dictCommande["startByte"]) + chr(self.Name)
        for chara in data:
            chara = chr(chara)
            payload = payload + chara
        payload = payload + chr(self.dictCommande["stopByte"])
        print("Payload:", payload)
        return payload

    def listen(self):
        data = self.readAll()
        self.decodeData(data)
        return data


if __name__ == "__main__":
    
    rc1 = RadioCommuncation(2)
    
# rc1 = RadioCommuncation(2)
# while True:
#   rc1.listen()

# rc1 = RadioCommuncation(1)
# while True:
#    rc1.send([rc1.dictCommande["Back"]])