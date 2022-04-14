import fake_rpi.smbus
#import smbus
from time import sleep 



AddressCOMPASS = 0x02
AddressPITCH = 0x04
AddressROLL = 0x05

class Compass:

    def __init__(self, messageRouter):
        self.messageRouter = messageRouter
        self.hardwareName = "Gyro"
        self.state = "ready"
        self.bus = smbus.SMBus(1) 
        self.Device_Address = 0x60  
        self.bus.write_byte_data(self.Device_Address, 0, 1)
    
    def get(self, command):
        if command == "state":
            return self.state
        if command == "COMPASS":
            return self.readRegister16bits(AddressCOMPASS)/10
            #print("Angle compass:", compass)
        elif command == "PITCH":
            return self.readRegister8bits(AddressPITCH)
            #print("Pitch :", compass)
        elif command == "ROLL":
            return self.readRegister8bits(AddressROLL)
        else:
            print("Unknow argument:", command)
            return None
        
    def readRegister16bits(self, addr):        
            high = self.bus.read_byte_data(self.Device_Address, addr)
            low = self.bus.read_byte_data(self.Device_Address, addr+1)
            value = ((high << 8) | low)
            if(value > 32768):
                    value = value - 65536
            return value
    
    def readRegister8bits(self, addr):        
        return self.bus.read_byte_data(self.Device_Address, addr)
       

if __name__ == "__main__":
    
    compass = Compass(None)
    compass.run()
    