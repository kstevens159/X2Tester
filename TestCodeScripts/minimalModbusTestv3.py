#!/usr/bin/env python3

import minimalmodbus
import datetime
import time
import struct

def main():

    ##Define port settings
##    x2mbAddress = 252
    x2mbAddress = 1
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
##    x2.debug=True

    ##Main Code
    
    #Test read/write
##    AddressChangeTest(x2,x2mbAddress)

    ReadClock(x2,x2mbAddress)
    
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

def ReadClock(x2,add):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing reading & writing Modbus address\n")

    #Read the current time
    print("Reading Time...")
    readResult = mbReadRetries(x2,0x701C,4)
    readTime=[readResult[0],readResult[1]] #The first two 16 bits are the time, the next two are the tz offset
##    convResult = two16ToOne32(readResult[0],readResult[1])
    convResult = combineFrom16Bits(readTime)
    print("The conv result is:",hex(convResult))
    formatedDateTime1 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult))
    if(readResult):
        print("The device's original time is",formatedDateTime1,"\n")
    else:
        print("The read was not successful\n")

    #Write the current system time
    print("Writing Current Time...")
    currentTime=int(time.time())
    formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(currentTime))
    print("Current computer time is:",formatedDateTime2)
##    timeIn16bit = one32toTwo16(currentTime)
    timeIn16bit = splitInto16Bits(currentTime)
    tzOffset=0x0000
    writeResult = mbWriteRetries(x2,0x701C,[timeIn16bit[0],timeIn16bit[1],0,0])
    if(writeResult):
        print("The write was successful\n")
    else:
        print("The write was not successful\n")

    #Read the current time
    print("Reading Time...")
    readResult = mbReadRetries(x2,0x701C,4)
    readTime=[readResult[0],readResult[1]] #The first two 16 bits are the time, the next two are the tz offset
##    convResult = two16ToOne32(readResult[0],readResult[1])
    convResult = combineFrom16Bits(readTime)
    formatedDateTime3 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult))
    if(readResult):
        print("The device's new time is",formatedDateTime3,"\n")
    else:
        print("The read was not successful\n")



def splitInto16Bits(combined):
    rawSeparate=struct.unpack('>4H',struct.pack('>Q',combined))
##    print(hex(rawSeparate[0]),hex(rawSeparate[1]),hex(rawSeparate[2]),hex(rawSeparate[3]))
    k=0
    separate=[]
    for i in range(0,4):
        if (rawSeparate[i] != 0):
            separate.append(rawSeparate[i])
            k=k+1  
    return separate

def combineFrom16Bits(separate):
    combined = 0
##    print(separate)
    k=len(separate)
##    print(k)
    for i in range(0,len(separate)):
        combined = combined + (separate[k-1]<<(16*i))
        k=k-1
    return combined


##def two16ToOne32(a16bit1,a16bit2):
##    first16hex = eval(hex(a16bit1))
##    a32bit = (a16bit1 << 16) + eval(hex(a16bit2))
##    return a32bit
##
##def one32toTwo16(a32bit):
##    a32bithex=eval(hex(a32bit))
##    a16bit1=(a32bithex >> 16)&0xffff
##    a16bit2=a32bithex&0xffff
##    return [a16bit1,a16bit2]
    
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
            device.serial.flushInput()
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
            device.serial.flushInput()
            result=device.write_registers(reg,value)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            device.serial.flushInput()
            time.sleep(0.5)
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return ['False']
    return value
            

#This function replaces the standard address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')

if __name__ == "__main__":
    main()



