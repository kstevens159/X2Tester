import minimalmodbus
from datetime import datetime
import time
import sys

##x2 = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
##time.sleep(1)
##readResult= x2.read_registers(0x1000,1,functioncode=4)
##print("The device's address is",readResult)

def main():

    #Define port settings
    x2mbAddress = 252
    baud = 19200
    parity = 'N'
    bytesize=8
    stopbits=1
    modbusTimeout=0.1
    comPort = '/dev/ttyUSB0'
    
    #Setup the modbus instance of the X2
    x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance mb
    minimalmodbus.BAUDRATE= baud
    minimalmodbus.PARITY=parity
    minimalmodbus.BYTESIZE=bytesize
    minimalmodbus.STOPBITS=stopbits
    minimalmodbus.TIMEOUT=modbusTimeout
    minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255
##    x2.debug=True

    #Test read/write
    AddressChangeTest(x2)

def AddressChangeTest(x2):
    print ("\n===================")
    print (datetime.now())
    print ("Testing reading & writing Modbus address")

    try:
        print("Reading address...")
        origAdd = x2.read_registers(0x1000,1,functioncode=4)
        print("The device's original address is",origAdd)

        if(origAdd==[1]): #if address is already 1
            add=[2]
            x2.write_registers(0x1000,add)#write address 2
        else:
            add=[1]
            x2.write_registers(0x1000,add)

        changeAdd=x2.read_regisers(0x1000,1,functioncode=4)

        print("The address was changed to", changeAdd)

    except Exception as err:
        print("An error occured on the address read:", err)    

#This function replaces the standard address range (0-247) check with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')

if __name__ == "__main__":
    main()



