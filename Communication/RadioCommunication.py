import RadioRobot

class RadioCommuncation:

    def __init__(self,Name):
        self.Name = Name
        self.Radio = RadioRobot.RadioRobot(Name)
        self.isIdle = True
        self.isSilent = False
        self.isReceiving = False
        self.isMaster = self.checkMaster()
        self.requestMessage = ["wantToSpeak"]
        self.receivedMessage = []
        self.dictCommande = {"startByte": 0x00,                  
                             "stopByte": 0xFF,
                             "wantToSpeak" : 0x10,
                             "PermissionToSpeak" : 0x11,
                             "TurnLeft" : 0x12,
                             "TurnRigth" : 0x13,
                             "Go" : 0x14,
                             "Back" : 0x15,
                            }# hexa : 0 , 255 , 16 , 17 

    def checkMaster(self):
        if self.Name == 1:
            return True
        return False

    def readAll(self):
        while True:
            payload = self.Radio.readAll()
            self.decodeData(payload)

    def write(self, listName, data):
        data = codeData(self,data)
        self.Radio.write(listName,data)
        
    def writeAll(self, listName, data):
        data = codeData(self,data)
        self.Radio.writeAll(data)

    def decodeData(self,data):
        node_id, message = self.convertData(data)
        if self.isMaster:
            if message == self.dictCommande["wantToSpeak"]:
                data = self.codeData([self.dictCommande["PermissionToSpeak"],node_id])
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
                
    def executeCmd(self,message):
        
        message = hex(ord(message))
        if message == hex(self.dictCommande["TurnLeft"]):
            print("Turn Left")
        if message == hex(self.dictCommande["TurnRigth"]):
            print("Turn Rigth")
        if message == hex(self.dictCommande["Go"]):
            print("Go")
        if message == hex(self.dictCommande["Back"]):
            print("Back")

            
    def convertData(self,data):
        node_id = data[0]
        message = data[2]
        node_id = data[1]
        return node_id, message

    def wantToSpeak(self,data):
        data = self.codeData(self.dictCommande["wantToSpeak"])
        self.write([0],data)

    def send(self,data):
        if self.isMaster:
            self.writeAll(data)
            return True
        else:
            if self.isSilent:
                return False
            if self.isIdle :
                data = self.codeData(data)
                self.wantToSpeak()
                response = self.readAll()
                self.decodeData(response)
                if self.asPermissionToSpeak:
                    self.write([0],data)
                    return True
        return False
        

    def codeData(self,data):
        data = chr(self.dictCommande["startByte"]) + chr(str(self.Name)) + chr(data) + chr(self.dictCommande["stopByte"])
        return data

    def listen(self):
        while True:
            data = self.readAll()
            self.decodeData(data)

rc1 = RadioCommuncation(2)
while True:
    rc1.listen()

rc2 = RadioCommuncation(1)
while True:
    rc2.send(self.dictCommande["Go"])

