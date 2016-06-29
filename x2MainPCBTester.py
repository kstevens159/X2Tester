#
# @file		        : x2MainPCBTester.py
# Project		: X2 Tester
# Author		: Kevin Stevens
# Created on	        : Jun 27, 2016
# Version		: 1.0
#
# Copyright (C) 2016 NexSens Technology, Inc.  All Rights Reserved.
#
# THIS SOURCE CODE FILE, DOCUMENTATION, AND INFORMATION THEREON ARE THE
# PROPERTY OF NEXSENS TECHNOLOGY, INCORPORATED.  ALL UNAUTHORIZED USE
# AND REPRODUCTION ARE STRICTLY PROHIBITED.
#
# --------------------------------------------------------------------------
# Description:
#	Used to test the X2 Main PCB's functionality at the CM. To be run
#       on a Raspberry Pi 3.
# 
#
# Revision Log:
# --------------------------------------------------------------------------
# MM/DD/YY hh:mm Who	Description
# --------------------------------------------------------------------------
# 06/28/16 09:00 KCS	Created
# --------------------------------------------------------------------------
#

#Imports
import datetime
import time
import os
import spidev
import x2mbRegisters as Reg
import minimalmodbus
import RPi.GPIO as GPIO

def main():

    ##############################
    ## Define program variables ##
    ##############################
    
    #Device Parameters
    snlen = 4 #length of the serial number
    mbRetries = 3
    #USB RS-485 Parameters
    x2mbAddress = 252
    baud = 19200
    parity = 'N'
    bytesize=8
    stopbits=1
    modbusTimeout=0.1
    comPort = '/dev/ttyUSB0'

    ################################
    ## Setup Devices & Interfaces ##
    ################################
    
    #Open SPI bus for use by the ADC chip
    spi = spidev.SpiDev()
    spi.open(0,0)

    #Setup the modbus instance of the X2
    x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance mb
    x2.serial.baudrate = baud
    x2.serial.parity = parity
    x2.serial.bytesize = bytesize
    x2.serial.stopbits = stopbits
    x2.serial.timeout = modbusTimeout
    minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255
##    x2.debug=True

    ##Define GPIO Interface
    GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
    #Define the pin numbers in a dictionary to allow easy reference
    pin = {"IO1"       :   11,
           "IO2"       :   13,
           "IO3"       :   15,
           "IO4"       :   12,
           "TRIGGER1"  :   16,
           "TRIGGER2"  :   18
           }
    #Set the GPIO directions
    GPIO.setup(pin["IO1"], GPIO.OUT)
    GPIO.setup(pin["IO2"], GPIO.OUT)
    GPIO.setup(pin["IO3"], GPIO.OUT)
    GPIO.setup(pin["IO4"], GPIO.OUT)
    GPIO.setup(pin["TRIGGER1"], GPIO.OUT)
    GPIO.setup(pin["TRIGGER2"], GPIO.OUT)
    
    ########################
    ## Create Output File ##
    ########################
    
    #Define the file name to be .../TestResults/<CURRENT_DATE>_PCBTestResults.csv
    name = "PCBTestResults.txt"
    date = datetime.datetime.now().strftime("%Y.%m.%d")
    relativePath = "/TestResults/"
    filename = os.path.dirname(__file__)+relativePath+date+"_"+name
    #Open the file
    if(os.path.isfile(filename)):   #If the file exists append it
        out_records=open(filename, 'a')
    else:                           #If the file doesn't exist create it and add section headers
        out_records=open(filename, 'w')
        out_records.write("Serial Number,"
                          "3V LDO Status,3V LDO Voltage,"
                          "Processor & Host RS-485 Status,"
                          "RTU Battery Status, RTU Battery Voltage,"
                          "3.3V SEPIC Status, 3.3V SEPIC Voltage,"
                          "EE Status,"
                          "Serial Flash Status,"
                          "SD Card Status\n")


    ###################
    ## PCB Test Loop ##
    ###################

    ##Continually loop through the test process to allow the user to test a batch of PCBs
    sn = getSN(snlen)
    while (sn != "-1"): #Loop through all PCBs to be tested
        out_records.write("%s" % sn) #Write serial number to file

        #Test the 3V LDO
        print("\n------------------------------")
        print("Testing the 3V LDO...")
        result=test3VLDO(spi) #Call the 3V LDO test module
        print("Test result:",result)
        out_records.write(",%s,%s" % (result[0],result[1])) #Write the result to the file
        print("------------------------------\n")

        #Test the RS-485 driver and processor
        print("\n------------------------------")
        print("Testing the Processor & RS-485 Modbus Communication...")
        result=testProcAndRS485(x2,mbRetries) #Call the Processor and RS-485 test module
        print("Test result:",result)
        out_records.write(",%s" % (result[0])) #Write the result to the file
        print("------------------------------\n")

##        #Test the RS-485 driver and processor
##        print("\n------------------------------")
##        print("Testing the Processor & RS-485 Modbus Communication...")
##        result=testProcAndRS485(x2,mbRetries) #Call the Processor and RS-485 test module
##        print("Test result:",result)
##        out_records.write(",%s" % (result[0])) #Write the result to the file
##        print("------------------------------\n")



        out_records.write("\n")#Line return to go to next record
        sn = getSN(snlen)

    #close the file
    out_records.close


###############
## Functions ##
###############

#Used to get the PCB's serial number and ensure it is valid
def getSN(snlen):
    #Get the SN from the user
    sn = input("Please enter the PCB's serial number (-1 if done): ")

    #Confirm the SN is the right number of digits
    i = True
    while (i): #Continue to loop until a valid SN is entered
        if (sn=="-1"):
            return sn
        if (len(sn) != snlen):
            sn = input("Please re-enter serial number. It must be %d characters (-1 if done): " % snlen)
        else:
            i = False       
    return sn

#This function is used to gracefully handle failed reads and allow retries 
def mbReadRetries(device,reg,numReg=1,retries=5):
    device.serial.flushInput() #clear serial buffer before starting
    for i in range (0,retries):
        try:
            result=device.read_registers(reg,numReg,functioncode=4)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            device.serial.flushInput()#Needed to clear the buffer before retrying. Otherwise the results are corrupted
            print("Reading",i,"Failed")
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return result

#This function is used to gracefully handle failed writes and allow retries 
def mbWriteRetries(device,reg,value,retries=5):
    device.serial.flushInput() #clear serial buffer before starting
    for i in range (0,retries):
        try:
            result=device.write_registers(reg,value)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            device.serial.flushInput() #Needed to clear the buffer before retrying. Otherwise the results are corrupted
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value

#Used to check the current status of the PCB's power and enable
#power if it is off
def power0on():
    #if(IO1==OFF):
        #IO1 = ON
        #time.sleep(1)
    return True

#Reads the analog voltage on a MCP3008 channel
#Also allows for a scaling value to be entered (default =1)
def readAnalog(spi,ch,scale=1): #ch must be 0-7
    adc = spi.xfer2([1,(8+ch)<<4,0]) #Read from MCP3008 chip
    data = ((adc[1]&3) << 8) + adc[2] #Convert to value

    volts = (data*3.3)/float(1023) #Convert to voltage
    volts = round(volts,2)#Rounds to two decimal places

    scaledVolts = volts*scale

    return scaledVolts


#Tests the 3V LDO is functioning correctly
def test3VLDO(spi):
    power0on()
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    
    analog0 = readAnalog(spi,0) #Read SPI0 ch. 0

    #Check if voltage is in range and return the result
    if (analog0 > 2.95):
        if (analog0 < 3.05):
            return ["Pass",analog0]
        else:
            return ["Fail-Voltage high",analog0]
    else:
        return ["Fail-Voltage low",analog0]

#Test that the RS-485 and processor are functioning correctly
def testProcAndRS485(x2,mbRetries):
    power0on()
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing reading & writing Modbus address\n")

    #Read the current address
    print("Reading address...")
    readResult = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
    if(readResult):
        print("The device's original address is",readResult[0],"\n")
    else:
        print("The read was not successful\n")
        return ["Fail"]

    #Write a new address
    print("Writing address...")
    if(readResult[0]==1): #If the current address is already 1, change to 2, then back to 1
        writeResult = mbWriteRetries(x2,Reg.mbReg["Add"][0],[2],retries=mbRetries)
        if(writeResult):
            print("The device's new address is",writeResult[0])
        else:
            print("The write was not successful\n")
            return ["Fail"]
        writeResult = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)#Change address back to 1
        time.sleep(0.01) #Without this the address doesn't read back right
        readResult = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
        if(readResult):
            print("The device's address was set back to",readResult[0],"\n")
            return ["Pass"]
        else:
            print("Resetting the address to %d was not successful\n" % writeResult[0])
            return ["Fail"]

    else: #If the address is anything besides 1, change to 1
        writeResult = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)
        if(writeResult):
            print("The device's new address is",writeResult[0],"\n")
            return ["Pass"]
        else:
            print("The write was not successful\n")
            return ["Fail"]
    

#This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')
            

if __name__ == "__main__":
    try:
        main()
        GPIO.cleanup()
    except KeyboardInterrupt:
        print("User cancelled with Keyboard")
        GPIO.cleanup()
    except Exception:
        print("An error occured")
        GPIO.cleanup()
        
