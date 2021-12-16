import serial
import os
from time import sleep


class Strompi:
    
    def __init__(self):
        
        self.breakS = 0.1
        self.breakL = 0.5

        self.serial_port = serial.Serial()

        self.serial_port.baudrate = 38400
        self.serial_port.port = "/dev/serial0"
        self.serial_port.timeout = 1
        self.serial_port.bytesize = 8
        self.serial_port.stopbits = 1
        self.serial_port.parity = serial.PARITY_NONE

        if self.serial_port.isOpen(): self.serial_port.close()
        self.serial_port.open()
    
    def shutdown(self):
        while True:
            self.serial_port.write(str.encode("quit"))
            sleep(self.breakS)
            self.serial_port.write(str.encode("\x0D"))
            sleep(self.breakL)

            self.serial_port.write(str.encode("poweroff"))
            sleep(self.breakS)
            self.serial_port.write(str.encode("\x0D"))

            print("sudo shutdown -h now")
            print("Shutting down...")

            sleep(2)
            os.system("sudo shutdown -h now")
            
    
if __name__ == "__main__":
    
    strompi = Strompi()
    strompi.shutdown()