#!/usr/bin/env python3

import minimalmodbus
import datetime
import time

def main():

    ##Define port settings
    x2mbAddress = 252
    baud = 19200
    parity = 'N'
    bytesize=8
    stopbits=1
    modbusTimeout=0.1
    comPort = '/dev/ttyUSB0'
    
    ##Setup the modbus instance of the X2
    x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance mb
    x2.serial.baudrate = baud
    x2.serial.parity = parity
    x2.serial.bytesize = bytesize
    x2.serial.stopbits = stopbits
    x2.serial.timeout = modbusTimeout
    minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255
    x2.debug=True

    ##Main Code
    
    #Test read/write
    AddressChangeTest(x2,x2mbAddress)

##    readResult = x2.read_registers(0x1000,1,functioncode=4)
####    readResult = mbReadRetries(x2,0x1000,1,3)
##    print(readResult)
##
##    try:
##        writeResult = x2.write_registers(0x1000,[1])
##    except:
##        writeResult = x2.write_registers(0x1000,[1])
####    writeResult = mbWriteRetries(x2,0x1000,[2],3)
##    print(writeResult)
##    
##    readResult = x2.read_registers(0x1000,1,functioncode=4)
####    readResult = mbReadRetries(x2,0x1000,1,3)
##    print(readResult)

    

    
##############################
########  FUNCTIONS  #########
##############################
    
def AddressChangeTest(x2,add):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing reading & writing Modbus address\n")

    #Read the current address
    print("Reading address...")
    readResult = mbReadRetries(x2,0x1000)
    if(readResult):
        print("The device's original address is",readResult[0],"\n")
    else:
        print("The read was not successful\n")

    #Write a new address
    print("Writing address...")
    if(readResult[0]==1): #If the current address is already 1, change to 2, then back to 1
        writeResult = mbWriteRetries(x2,0x1000,[2])
        if(writeResult):
            print("The device's new address is",writeResult[0])
        else:
            print("The write was not successful\n")
        writeResult = mbWriteRetries(x2,0x1000,[1])#Change address back to 1
        if(writeResult):
            print("The device's address was set back to",writeResult[0],"\n")
        else:
            print("Resetting the address to %d was not successful\n" % writeResult[0])
    else: #If the address is anything besides 1, change to 1
        writeResult = mbWriteRetries(x2,0x1000,[1])
        if(writeResult):
            print("The device's new address is",writeResult[0],"\n")
        else:
            print("The write was not successful\n")

    #Read the current address again
    print("Reading address...")
    readResult = mbReadRetries(x2,0x1000)
    if(readResult):
        print("The device's final address is",readResult[0],"\n")
    else:
        print("The read was not successful\n")

#This function is used to gracefully handle failed reads and allow retries 
def mbReadRetries(device,reg,numReg=1,retries=3):
    for i in range (0,retries):
        try:
            result=device.read_registers(reg,numReg,functioncode=4)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            device.serial.flushInput()
            time.sleep(1)
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return result

#This function is used to gracefully handle failed writes and allow retries 
def mbWriteRetries(device,reg,value,retries=3):
    for i in range (0,retries):
        try:
            result=device.write_registers(reg,value)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            device.serial.flushInput()
            time.sleep(0.5)
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value
            

#This function replaces the standard address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')

if __name__ == "__main__":
    main()


