class MessageDecoder:
    
    def decode(self, messageReceived):
        payload = []
        for i, data in enumerate(messageReceive):
            payload.append(int(hex(ord(data)), 16))
        return payload
    
        
            action = payload[0]
            print("action", action)
            if action == self.rc.dictCommande["SCAN"]:
                self.logContent += " SCAN"
                self.scanLidar()
                
            if action == self.rc.dictCommande["PHOTO"]:
                self.logContent += " PHOTO"
                self.cameraPhoto()
                
            if action == self.rc.dictCommande["RUN"]:
                self.incrementFileNb()
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                self.logContent += " RUN " + payload
                self.commandMotorReceived("RUN", payload)

            if action == self.rc.dictCommande["TURN"]:
                self.incrementFileNb()
                payload[2] = payload[1] + payload[2] / 100
                payload = payload[2:]
                print("timeMove", payload[0], end=" ")
                print("direction", payload[1], end=" ")
                print("initSpeed", payload[2], end=" ")
                print("maxSpeed", payload[3], end=" ")
                print("finalSpeed", payload[4], end=" ")
                print("maxSpeedRot", payload[5])
                self.logContent += " TURN " + payload
                self.commandMotorReceived("TURN", payload)

            if action == self.rc.dictCommande["STOP"]:
                self.commandMotorReceived("STOP", [""])
        print("Drive motor finish")