import smbus
from time import sleep 


AddressCOMPASS = 0x02
AddressPITCH = 0x04
AddressROLL = 0x05

class Compass:

    def __init__(self):
        self.bus = smbus.SMBus(1) 
        self.Device_Address = 0x60  
        self.bus.write_byte_data(self.Device_Address, 0, 1)

    def readRegister16bits(self, addr):        
            high = self.bus.read_byte_data(self.Device_Address, addr)
            low = self.bus.read_byte_data(self.Device_Address, addr+1)
            value = ((high << 8) | low)
            if(value > 32768):
                    value = value - 65536
            return value
    
    def readRegister8bits(self, addr):        
        return self.bus.read_byte_data(self.Device_Address, addr)
       

    def run(self, arg):
        if arg == "COMPASS":
            return self.readRegister16bits(AddressCOMPASS)/10
            #print("Angle compass:", compass)
        elif arg == "PITCH":
            return self.readRegister8bits(AddressPITCH)
            #print("Pitch :", compass)
        elif arg == "ROLL":
            return self.readRegister8bits(AddressROLL)
        else:
            print("Unknow argument:", arg)
            return None


if __name__ == "__main__":
    
    compass = Compass()
    compass.run()
    