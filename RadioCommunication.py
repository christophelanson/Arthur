import RadioRobot.py

class RadioCommuncation:

	def __init__(self,Name):
		self.Name = Name
		self.Radio = RadioRobot(Name)
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
							}

	def checkMaster(self):
		if self.Name = 1:
			return True
		return False

	def readAll(self, listName):
		while True:
			node_id, payload = self.Radio.readAll()
			if not self.isReceiving:
				if payload != self.dictCommande["startByte"]:
					pass
				if payload == self.dictCommande["startByte"]:
					self.isReceiving = True
					self.receivedMessage.append(payload)

			elif self.isReceiving:
				if payload == self.dictCommande["stopByte"]:
					self.receivedMessage.append(payload)
					self.isReceiving = False
					data = [node_id, payload]
					return data
				else:
					self.receivedMessage.append(payload)
		
	def concatenateMessage(self):

	def write(self, listName, data):
		for byte in data:
			self.Radio.write(listName,byte)

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
					self.asPermissionToSpeak = False
				else:
					self.asPermissionToSpeak = False
					self.isSilent = True

	def convertData(self,payload):
		node_id = data[0]
		payload = data[1]
		message = payload[1:-1]
		return node_id, message

	def wantToSpeak(self,data):
		data = self.codeData(self.dictCommande[self.requestMessage])
		self.write([0],data)

	def send(self,data):
		if self.isSilent:
			return False
		if self.isIdle :
			data = self.codeData(data)
			self.wantToSpeak()
			data = self.readAll()
			self.decodeData(data)
			if self.asPermissionToSpeak:
				self.write([0],self.message)
				return True

	def codeData(self,data):
		data = self.dictCommande["startByte"] + data + self.dictCommande["stopByte"]
		return data

	def listen(self):
		while True:
			data = self.readAll()
			self.decodeData(data)


