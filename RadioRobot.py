from circuitpython_nrf24l01.rf24 import RF24
import board
import digitalio
import copy

class RadioRobot:

	def __init__(self, Name):

		self.dictAllAddress = {1:b"1Node", 2:b"2Node"}
		self.initSpi()
		self.Name, self.dictAddress, self.ownAddress = self.setIdentity(Name)


	def initSpi(self):
		# change these (digital output) pins accordingly
		ce = digitalio.DigitalInOut(board.D4)
		csn = digitalio.DigitalInOut(board.D5)

		# using board.SPI() automatically selects the MCU's
		# available SPI pins, board.SCK, board.MOSI, board.MISO
		spi = board.SPI()  # init spi bus object

		# we'll be using the dynamic payload size feature (enabled by default)
		# initialize the nRF24L01 on the spi bus object
		nrf = RF24(spi, csn, ce)

		# set the Power Amplifier level to -12 dBm since this test example is
		# usually run with nRF24L01 transceivers in close proximity
		nrf.pa_level = -12

	def setIdentity(self, Name):
			dictAddressTx = copy.deepcopy(self.dictAllAddress)
			dictAddressTx.pop(Name)
			dictAddressRx["me"] = self.dictAllAddress[Name]
			return dictAddressTx, dictAddressRx

	def openListenChanel(self, dictAddress):
		for name in dictAddress.keys():
        	nrf.open_rx_pipe(name, dictAddress[name])
        nrf.listen = True 

    def listenChanel(self):
    	while True:
	    	while not nrf.fifo(False, True):  # keep RX FIFO empty for reception
	            # show the pipe number that received the payload
	            # NOTE read() clears the pipe number and payload length data
	            print("Received", nrf.any(), "on pipe", nrf.pipe, end=" ")
	            node_id, payload_id = struct.unpack("<ii", nrf.read())
	            print("from node {}. PayloadID: {}".format(node_id, payload_id))
	        return node_id, payload_id

    def openSpeakChanel(self, dictAddress):
    	nrf.listen = False
		for name in dictAddress.keys():
        	nrf.open_tx_pipe(name, dictAddress[name])
         
    def speakChanel(self, data, dictAddress):
    	for name in dictAddress.keys():
	    	payload = struct.pack("<ii", dictAddress[name], data)
	        # show something to see it isn't frozen
	        start_timer = time.monotonic_ns()
	        report = nrf.send(payload)
	        end_timer = time.monotonic_ns()
	        # show something to see it isn't frozen
	        if report:
	            print(
	                "Transmission of payloadID {} as node {} successfull! "
	                "Transmission time: {} us".format(
	                    counter, name, (end_timer - start_timer) / 1000
	                )
	            )
	        else:
	            print("Transmission failed or timed out")

    def read(self, listName):
    	dictAddressRead = {}
    	for name in listName
    		dictAddressRead[name] = self.dictAddress[name]
    	self.openListenChanel(dictAddressRead)
    	node_id, payload = self.listenChanel()
    	return node_id, payload

    def readAll(self):
    	self.openListenChanel(self.dictAddress)
    	node_id, payload = self.listenChanel()
    	return node_id, payload

   	def write(self, listName, data):
   		dictAddressWrite = {}
    	for name in listName
    		dictAddressWrite[name] = self.dictAddress[name]
    	self.openSpeakChanel(dictAddressWrite)
    	self.speakChanel(data,dictAddressWrite)

    def writeAll(self, data):
    	self.openSpeakChanel(self.dictAddress)
    	self.speakChanel(data,self.dictAddress)


RadioRobot1 = RadioRobot(1)
RadioRobot1.read([2])

RadioRobot2 = RadioRobot(2)
RadioRobot2.write([1],"salut")
