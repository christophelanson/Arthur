from HardwareHandler.HardwareHandler import HardwareHandler
from colorama import Fore  #Permet de print en couleur

class MessageRouter:
    
    def __init__(self,node, hardwareHandler: HardwareHandler):
        self.node = node
        self.hardwareHandler = hardwareHandler
        self.dictMessage = {}
        self.dictCommand =   { 
                "RUN": "A",
                "TURN": "B",
                "STOP": "C",
                "SEND": "D",
                "getState": "E"
            }
        self.invDictCommand = dict((v,k) for k,v in self.dictCommand.items())
    

    def updateHardware(self):
        for hardware in self.hardwareHandler.hardwareDict.keys():
            self.dictMessage[self.hardwareHandler.hardwareDict[hardware].hardwareId]= {}
            self.dictMessage[self.hardwareHandler.hardwareDict[hardware].hardwareId]["message"] = ""
            self.dictMessage[self.hardwareHandler.hardwareDict[hardware].hardwareId]["isReceived"] = False
            self.dictMessage[self.hardwareHandler.hardwareDict[hardware].hardwareId]["Name"] = hardware

    def route(self, senderName, receiverName, hardwareName, command, isReturn, channel=None):
        hardwareId = self.hardwareHandler.hardwareDict[hardwareName].hardwareId
        if senderName == receiverName:
            return self.hardwareHandler.sendInstruction(hardwareName, command, isReturn)
        
        if senderName != receiverName:
            command = self.codeMessageRadio(senderName, receiverName, hardwareName, command, isReturn, isResponse=isReturn)
            self.hardwareHandler.sendInstruction(channel, command, isReturn = 0) 
            if isReturn:
                print(f"{Fore.GREEN}INFO (radio) -> will wait for data...")               
                while self.dictMessage[hardwareId]["isReceived"] == False: #[hardware]
                    pass
                message = self.dictMessage[hardwareId]["message"]
                self.dictMessage[hardwareId]["message"] = ""
                self.dictMessage[hardwareId]["isReceived"] = False
                return message
            
    #Si la command vient de l'exterieur
    def unroute(self, messageReceived, channel):
        senderName, receiverName, hardwareId, command, isReturn, isResponse = self.decodeMessageRadio(messageReceived)
        print(f"{Fore.GREEN}INFO (radio) -> Payload received {messageReceived} from {senderName} to {receiverName}")
        print(f"{Fore.GREEN}INFO (radio) -> Target: {hardwareId}")
        print(f"{Fore.GREEN}INFO (radio) -> Command to do: {command}")
        print(f"{Fore.GREEN}INFO (radio) -> Need a return data ? {isReturn}")
        print(f"{Fore.GREEN}INFO (radio) -> Is it a received message ? {isResponse}")

        hardwareName = self.hardwareHandler.hardwareDictId[hardwareId]
        if isResponse:
            self.dictMessage[hardwareId]["message"] = command
            self.dictMessage[hardwareId]["isReceived"] = True
        else :
            if not isReturn:
                
                self.hardwareHandler.sendInstruction(hardwareName, command, isReturn)
            else:
                returnData = self.hardwareHandler.sendInstruction(hardwareName, command, isReturn)
                command = self.codeReturnRadio(senderName, receiverName, hardwareName, str(returnData), isReturn = 0, isResponse =1)
                self.hardwareHandler.sendInstruction(channel, command, isReturn = False) #isSet            
    
    def decodeMessageRadio(self, messageReceived):
        messageReceived = messageReceived.decode()
        senderName = messageReceived[0]
        receiverName = messageReceived[1]
        hardwareId = int(messageReceived[2])
        command = self.invDictCommand[messageReceived[3]]
        isReturn = int(messageReceived[4])
        isResponse = int(messageReceived[5])
        return senderName, receiverName, hardwareId, command, isReturn, isResponse
    
    def codeMessageRadio(self, senderName, receiverName, hardwareName,  command, isReturn, isResponse):
        hardwareId = self.hardwareHandler.hardwareDict[hardwareName].hardwareId
        return str(self.dictCommand["SEND"]) + str(senderName) + str(receiverName) + str(hardwareId) + str(self.dictCommand[command]) + str(isReturn )+ str(isResponse)
    
    def codeReturnRadio(self, senderName, receiverName, hardwareName,  returnData, isReturn, isResponse):
        hardwareId = self.hardwareHandler.hardwareDict[hardwareName].hardwareId
        return str(self.dictCommand["SEND"]) + str(senderName) + str(receiverName) + str(hardwareId) + returnData + str(isReturn)+ str(isResponse)
        
        
    