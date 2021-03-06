#!/usr/bin/env python3

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
from wifi import Cell
import struct


def main():
    try:

        ##############################
        ## Define program variables ##
        ##############################
        
        #Device Parameters
        snlen = 4 #length of the serial number
        mbRetries = 3 #Number of retries on modbus commands
        wifiRetries = 10
        wifiNetwork = "X2 Logger"
##        wifiNetwork = "ZyXEL"
        #USB RS-485 Parameters
        x2mbAddress = 252 #X2 Main universal address
        baud = 19200
        parity = 'N'
        bytesize=8
        stopbits=1
        modbusTimeout=0.5
        comPort = '/dev/ttyUSB0'

        ################################
        ## Setup Devices & Interfaces ##
        ################################
        
        #Open SPI bus for use by the ADC chip
        spi = spidev.SpiDev()
        spi.open(0,0)

        #Setup the modbus instance of the X2
        x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance
        x2.serial.baudrate = baud
        x2.serial.parity = parity
        x2.serial.bytesize = bytesize
        x2.serial.stopbits = stopbits
        x2.serial.timeout = modbusTimeout
        minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255
        x2.debug=True

        ##Define GPIO Interface
        GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
        GPIO.setwarnings(False)
        #Define the pin numbers in a dictionary to allow easy reference
        pinDict = {"IO1"        :   11,
                   "IO2"        :   13,
                   "IO3"        :   15,
                   "IO4"        :   12,
                   "TRIGGER1"   :   16,
                   "TRIGGER2"   :   18
                  }
        #Set the GPIO directions
        GPIO.setup(pinDict["IO1"], GPIO.OUT)
        GPIO.setup(pinDict["IO2"], GPIO.OUT)
        GPIO.setup(pinDict["IO3"], GPIO.OUT)
        GPIO.setup(pinDict["IO4"], GPIO.OUT)
        GPIO.setup(pinDict["TRIGGER1"], GPIO.OUT)
        GPIO.setup(pinDict["TRIGGER2"], GPIO.OUT)
        
        ##Functions
        powerOn(x2,mbRetries,GPIO,pinDict,"IO1",delay=2.0)
##        time.sleep(2)
##        readResult1 = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries)
##        print(readResult1)
        

    #Define operation when an exception occurs
    except KeyboardInterrupt:
        GPIO.cleanup() #Clean up GPIOs
        print("\n==============================\n")
        print("The program was cancelled by a keyboard interrupt!\n")
        print("==============================\n")
        input("Press Enter to exit\n")
    except Exception as error:
        print("\n==============================\n")
        print("The program encountered the following error!\n")
        print("Error Type: ", type(error))
        print(error.args)
        print(error)
        print("==============================\n")
        input("Press Enter to exit\n")
    finally:
        print("Cleaning up and exiting...")
##        GPIO.output(pinDict["IO1"],GPIO.LOW) #Turn power off to Primary Power
##        GPIO.output(pinDict["IO2"],GPIO.LOW) #Turn power off to Secondary Power
##        GPIO.output(pinDict["IO3"],GPIO.LOW) #Turn power off to Backup Power
##        GPIO.output(pinDict["IO4"],GPIO.LOW) #Turn power off to T-Node
        GPIO.cleanup() #Clean up GPIOs



###############
## Functions ##
###############

# This function is able to take up to 4 16-bit hex values as a list and
# combine them into a single value
def combineFrom16Bits(separate):
    # Loop through all the sent values and add them to the end value
    combined = 0
    k=len(separate)
    for i in range(0,len(separate)):
        combined = combined + (separate[k-1]<<(16*i)) #Shift by 16-bits times the location
        k=k-1
    return combined

#Generic function to check a status register on the X2
def checkStatus(x2,mbRetries,mbDictName,clearText):
    #Read the Status
    print("Reading",clearText,"Status...")
    readResult = mbReadRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries)
    if(readResult):
        if(readResult[0]==1):
            print("The",clearText,"status is good")
            return [readResult[0],"Pass"]
        elif(readResult[0]==0):
            print("The",clearText,"status is bad")
            return [readResult[0],"Fail-The "+clearText+" status was returned as bad"]
        else:
            print("The",clearText,"status is unknown")
            return [readResult[0],"Fail-The "+clearText+" status was returned as an unknown value"]
    else:
        print("The read was not successful")
        return [-999999,"Fail-The Modbus read failed. No status received"]

#Generic function to enable or disable any of the X2's switches
def enableDisable(x2,mbRetries,mbDictName,clearText,onOff):
    #Modbus Device, # MB retries, MB Dictionary Name, Readable text, True=On/False=Off
    
    #Toggle the switch
    if(onOff):
        #Turn the switch on
        print("Enabling the",clearText,"...")
        writeResult1 = mbWriteRetries(x2,Reg.mbReg[mbDictName][0],[1],retries=mbRetries) #1=on
        if(writeResult1):
            print("The",clearText,"was successfully enabled")
            return True
        else:
            print("Enabling the",clearText,"was not successful")
            return False
    else:
        #Turn the switch off
        print("Disabling the",clearText,"...")
        writeResult2 = mbWriteRetries(x2,Reg.mbReg[mbDictName][0],[0],retries=mbRetries) #0=off
        if(writeResult2):
            print("The",clearText,"was successfully disabled")
            return True
        else:
            print("Disabling the",clearText,"was not successful")
            return False

#Used to get the PCB's serial number and ensure it is valid
def getSN(snlen):
    #Get the SN from the user
    sn = input("Please do the following (Enter -1 if done):\n"
               "1) Insert the SD Card\n"
               "2) Connect the PCB\n"
               "3) Enter the PCB's serial number\n"
               "Serial Number: ")

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
def mbReadRetries(device,reg,numReg=1,retries=5): #(Minimalmodbus device),(Register address),(Number of registers to read),(Retry attempts)
    for i in range (0,retries):
        try:
            device.serial.flushInput() #clear serial buffer before reading
            result=device.read_registers(reg,numReg,functioncode=4)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            print("Reading",i,"Failed")
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return result
#Returns False if it fails and the read values if successful

#This function is used to gracefully handle failed writes and allow retries 
def mbWriteRetries(device,reg,value,retries=5): #(Minimalmodbus device),(Register address),(List of values to write),(Retry attempts)
    for i in range (0,retries):
        try:
            device.serial.flushInput() #clear serial buffer before writing
            device.write_registers(reg,value)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value
#Returns False if it fails and the values that were written if successful

#Used to check the current status of the PCB's power and disable
#power if it is on
def powerOff(GPIO,pinDict,pinValue):
    if(GPIO.input(pinDict[pinValue])== 1):
        GPIO.output(pinDict[pinValue],GPIO.LOW)
    return True

#Used to check the current status of the PCB's power and enable
#power if it is off
def powerOn(x2,mbRetries,GPIO,pinDict,pinValue,delay=2.0):
    if(GPIO.input(pinDict[pinValue])== 0):
        GPIO.output(pinDict[pinValue],GPIO.HIGH)
        #The sleep time of 1 works in IDLE, but not in the cmd line
        #Not sure reason, but possible execution speed is faster in cmd line
        time.sleep(delay)
        enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)#Turn off the Wi-Fi so it doesn't interfere on the RS-485 bus
    return True

#Tests the voltage and valid line status for a power input channel
def prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,mbDictName,validCheck,validValue):
    #Read the Channel Voltage
    print("Reading Channel Voltage...")
    readResult1 = mbReadRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries)
    if(readResult1):
        chVoltage=combineFrom16Bits(readResult1)
        print("The channel voltage level is",chVoltage,"\n")
        
        #Check if voltage is in range
        rangeCheck=valueRangeCheck(12.0,0.25,chVoltage)#Expected, tolerance, test input
        chVoltageStat=rangeCheck[0]#True if in range and False if out of range
    else:
        print("The channel voltage read was not successful\n")
        chVoltage="Fail-Reading the channel voltage was not successful"
        chVoltageStat=False

    if(validCheck):#Only try if the 3.3V SEPIC was turned on successfully
        #Read the Valid Lines
        print("\nReading the valid lines")
        readResult2 = mbReadRetries(x2,Reg.mbReg["Valid"][0],Reg.mbReg["Valid"][1],retries=mbRetries)
        if(readResult2): 
            if(readResult2[0]== validValue): #If read was successful check the correct lines are enabled
                print("The correct valid lines were enabled")
                chValid=readResult2[0]
                chValidStat=True
            else:
                print("The incorrect valid lines were enabled")
                chValid=readResult2[0]
                chValidStat=False
        else:
            print("Reading the valid lines was not successful")
            chValid="Fail-Reading the valid lines was not successful"
            chValidStat=False
    else:
        chValidStat=False
        chValid="Fail-Enabling 3.3V SEPIC was not successful"

    #Check if the overall input was successful
    if(chVoltageStat and chValidStat):
        chStat="Pass"
    else:
        chStat="Fail-Channel voltage returned %s and channel valid returned %s" % (chVoltageStat,chValidStat)

    return [chStat,chVoltage,chValid]

#Reads the analog voltage on a MCP3008 channel
#Also allows for a scaling value to be entered (default =1)
def readAnalog(spi,ch,scale=1): #ch must be 0-7
    adc = spi.xfer2([1,(8+ch)<<4,0]) #Read from MCP3008 chip
    data = ((adc[1]&3) << 8) + adc[2] #Convert to value

    volts = (data*3.3)/float(1023) #Convert to voltage
    volts = round(volts,2)#Rounds to two decimal places

    scaledVolts = volts*scale

    return scaledVolts

# This function take a 16-64 bit value and split it into a list of 16-bit values
def splitInto16Bits(combined):
    #Take the values and pack and unpack them appropriatly to get a list of 16-bit hex values
    rawSeparate=struct.unpack('>4H',struct.pack('>Q',combined))

    #Loop through the list and remove any 0 values from the front of the list
    k=0
    separate=[]
    for i in range(0,4):
        if (rawSeparate[i] != 0):
            separate.append(rawSeparate[i])
            k=k+1  
    return separate

#Test if a read voltage falls in a certain range
def valueRangeCheck(level,threshold,read):
    #Expected value, tolerance, input to test
    
    print("Checking reading is in range...")
    if (read > level-threshold):
        if (read < level+threshold):
            print("Reading is in range. It is",read)
            return [True,"Pass"]
        else:
            print("Reading is too high. It is",read)
            return [False,"Fail-Reading high"]
    else:
        print("Reading is too low. It is",read)
        return [False,"Fail-Reading low"]    


#-----------------------------------#

#Test the 12V SEPIC
def test12SEPIC(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing 12V SEPIC...\n")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Read the 12V SEPIC voltage
    print("Reading 12V SEPIC Voltage...")
    readResult = mbReadRetries(x2,Reg.mbReg["12VSen_V"][0],Reg.mbReg["12VSen_V"][1],retries=mbRetries)
    if(readResult):
        voltage = combineFrom16Bits(readResult)
        print("The 12V SEPIC voltage level is",voltage,"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(12,0.25,voltage)#Expected, tolerance, test input

        return[rangeCheck[1],voltage]
    else:
        print("The 12V SEPIC voltage read was not successful\n")
        return ["Fail-Reading the 12V SEPIC voltage was not successful",-999999]
    
#Test the 3.3V SEPIC
def test33SEPIC(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing 3.3V SEPIC...\n")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1) == False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the 3.3V SEPIC voltage
    print("Reading 3.3V SEPIC Voltage...")
    readResult = mbReadRetries(x2,Reg.mbReg["VCC33_V"][0],Reg.mbReg["VCC33_V"][1],retries=mbRetries)
    if(readResult):
        voltage = combineFrom16Bits(readResult)
        print("The 3.3V SEPIC voltage level is",voltage,"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(3.3,0.1,voltage)#Expected, tolerance, test input

        return[rangeCheck[1],voltage]
    else:
        print("The 3.3V SEPIC voltage read was not successful\n")
        return ["Fail-Reading the 3.3V SEPIC voltage was not successful",-999999]

#Test the 3V LDO is functioning correctly
def test3VLDO(GPIO,pinDict,spi):   
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing 3V LDO\n")

    print("Reading 3V LDO Voltage...")
    analog0 = readAnalog(spi,0) #Read SPI0 ch. 0
    print("The read voltage is",analog0,"\n")

    #Check if voltage is in range and return the result
    rangeCheck=valueRangeCheck(3.0,0.05,analog0)#Expected, tolerance, test input

    return[rangeCheck[1],analog0]

#Test the priority power switch is working correctly
def testPrioPwrSW(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO3",delay=0)#Enable the backup power input
    powerOff(GPIO,pinDict,"IO1")#Ensure Primary input is off
    powerOff(GPIO,pinDict,"IO2")#Ensure Secondary input is off
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")

    #Enable 3.3V SEPIC and set a flag on whether to test the valid lines
    validCheck = enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)

    ##Test backup input
    print("\nTesting the Backup Input...\n")
    [bakStat,bakVoltage,bakValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"BakPwr_V",validCheck,0b100)

    ##Test secondary input
    powerOn(GPIO,pinDict,"IO2",delay=0)#Enable secondary input
    
    print("\nTesting the Secondary Input...\n")
    [secStat,secVoltage,secValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"SecPwr_V",validCheck,0b110)

    ##Test primary input
    powerOn(GPIO,pinDict,"IO1",delay=0)#Enable primary input
    
    print("\nTesting the Primary Input...\n")
    [priStat,priVoltage,priValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"PriPwr_V",validCheck,0b111)

    ##Test PPP_1DISCON
    print("Triggering disconnect of Primary Power...")

    #Enabled the PPP_1DISCON pin to pull UV of Primary to GND
    writeResult = mbWriteRetries(x2,Reg.mbReg["PPP_Dis"][0],[1],retries=mbRetries)#0=pri on; 1=pri off
    if(writeResult):
        print("The primary power has been disabled")
        #Read the valid lines
        readResult = mbReadRetries(x2,Reg.mbReg["Valid"][0],Reg.mbReg["Valid"][1],retries=mbRetries)
        if(readResult):
            PPP_DisValid=readResult[0]
            if(readResult[0]== 0b110): #If read was successful check the correct lines are enabled
                print("The correct valid lines were enabled")
                PPP_DisStatus="Pass"
            else:
                print("The incorrect valid lines were enabled")
                PPP_DisStatus="Fail-The incorrect valid lines were set"
        else:
            print("Reading the valid lines was not successful")
            PPP_DisStatus="Fail-Reading the valid lines was not successful"
            PPP_DisValid=-999999
    else:
        print("The write was not successful")
        PPP_DisStatus="Fail-Disabling primary power failed"
        PPP_DisValid=-999999
    

    #Disable secondary and backup inputs
    powerOff(GPIO,pinDict,"IO2")
    powerOff(GPIO,pinDict,"IO3")

    return [bakStat,bakVoltage,bakValid,secStat,secVoltage,secValid,priStat,priVoltage,priValid,PPP_DisStatus,PPP_DisValid]


#Test that the RS-485 and processor are functioning correctly
def testProcEEAndRS485(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing reading & writing Modbus address\n")

    #Read the current address
    print("Reading address...")
    readResult1 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
    if(readResult1):
        print("The device's original address is",readResult1[0],"\n")
    else:
        print("The read was not successful\n")
        return ["Fail-Initial read was not successful","Fail-EE not tested"]

    #Write a new address
    print("Writing address...")
    if(readResult1[0]==1): #If the current address is already 1, change to 2, then back to 1
        writeResult1 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[2],retries=mbRetries)
        if(writeResult1):
            print("The device's new address is",writeResult1[0])
        else:
            print("The write was not successful")
            return ["Fail-Writing address was not successful","Fail-EE not tested"]

        #Cycle the power to confirm address is written to and can be read from EE
        print("\nTesting EE Chip")
        print("Power cycling to confirm EE works...")
        powerOff(GPIO,pinDict,"IO1")
        print("Power off.\nWaiting 1 second")
        time.sleep(1)
        powerOn(GPIO,pinDict,"IO1")
        print("Power on")

        #Read address and confirm it is still 2 after the power cycle
        readResult2 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
        if(readResult2):
            print("The devices address is now",readResult2[0])
            if(readResult2[0]==2):
                print("The address was retained on power cycle")
                EEResult="Pass"
            else:
                print("The address was not retained on power cycle. EE Test Failed.")
                EEResult="Fail-Address not retained in EE"
        else:
            print("Reading address after EE power cycle was not successful")
            EEResult = "Fail-EE not tested"
            return ["Fail-Reading address after EE power cycle was not successful",EEResult]
        
        
        writeResult2 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)#Change address back to 1
        if(writeResult2):
            print("The device's address was set back to",writeResult2[0])
        else:
            print("The write was not successful")
            return ["Fail-Changing address back to 1 was not successful",EEResult]
        time.sleep(0.01) #Without this the address doesn't read back right
        readResult3 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
        if(readResult3):
            print("The device's final address is",readResult3[0])
            return ["Pass",EEResult]
        else:
            print("Resetting the address to %d was not successful" % writeResult2[0])
            return ["Fail-Final read was not successful",EEResult]

    else: #If the address is anything besides 1, change to 1
        writeResult3 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)
        if(writeResult3):
            print("The device's new address is",writeResult3[0])
            return ["Pass","Pass"] #Assume EE is OK, since address started as a non default value (1)
        else:
            print("The write was not successful")
            return ["Fail-Writing address was not successful","Pass"] #Assume EE is OK, since address started as a non default value (1)

#Test RTC Battery Functionality
def testRTC(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
  
    #Read the RTC Voltage
    print("Reading the RTC Voltage...")
    RTCRawResult = mbReadRetries(x2,Reg.mbReg["RTCBAT_V"][0],Reg.mbReg["RTCBAT_V"][1],retries=mbRetries)
    if(RTCRawResult):
        RTCVoltageValueResult = combineFrom16Bits(RTCRawResult)
        print("The RTC Battery voltage is",RTCVoltageValueResult,"\n")
        [rangeCheck,RTCVoltageRangeResult]=valueRangeCheck(3.0,0.2,RTCVoltageValueResult)
    else:
        print("The RTC Battery voltage read was not successful\n")
        RTCVoltageValueResult=-999999
        RTCVoltageRangeResult="Fail-Voltage read not successful"

    #Read the current time
    print("Reading Time from X2...")
    initialTimeReadResult = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries) #Read from the X2
    if(initialTimeReadResult):
        readTime1=[initialTimeReadResult[0],initialTimeReadResult[1]] #The first two 16 bits are the time, the next two are the tz offset
        convResult1 = combineFrom16Bits(readTime1) #Convert to a single 32-bit time
        formatedDateTime1 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult1)) # Convert from Epoch to readable
        print("The device's original time is",formatedDateTime1,"\n")

        #Write the current system time
        print("Writing Current Time...")
        currentPCTime=int(time.time()) #Read the current time from the system
        formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(currentPCTime)) # Convert from Epoch to readable
        print("Current computer time is:",formatedDateTime2)
        timeIn16bit = splitInto16Bits(currentPCTime) # Convert into separate 16-bit values
        tzOffset1=0 # Set the time zone offset to 0 for UTC time
        tzOffset2=0
        writeResult = mbWriteRetries(x2,Reg.mbReg["SetTime"][0],[timeIn16bit[0],timeIn16bit[1],tzOffset1,tzOffset2]) #Write to X2
        if(writeResult):
            print("Writing current computer time to X2 was successful\n")

            #Check if the board keeps time on a power cycle
            print("Cycling Power to board...")
            powerOff(GPIO,pinDict,"IO1")
            print("Waiting 1 seconds...")
            time.sleep(1)
            print("Turning board back on and checking time is accurate\n")
            powerOn(GPIO,pinDict,"IO1")

            #Read the boards current time
            print("Reading Time from X2...")
            finalTimeReadResult = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries) #Read from the X2
            if(finalTimeReadResult):
                readTime2=[finalTimeReadResult[0],finalTimeReadResult[1]] #The first two 16 bits are the time, the next two are the tz offset
                convResult2 = combineFrom16Bits(readTime2) #Convert to a single 32-bit time
                formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult2)) # Convert from Epoch to readable
                print("The device's final time is",formatedDateTime2,"\n")

                timeDiff = convResult2 - int(time.time()) #Determine if time is saved

                if (timeDiff >= -5 and timeDiff <= 5):
                    print("Success! The RTC Clock was",timeDiff,"seconds off")
                    timeDiffResult="Pass"
                else: #If time difference is wrong
                    print("Failure! The RTC Clock was",timeDiff,"seconds off")
                    timeDiffResult="Fail"
            else: #If final time read fails
                print("The final time read was not successful\n")
                timeDiff=-999999
                timeDiffResult="Fail-Final time read not successful"
        else: #if time write fails
            print("The time write was not successful\n")
            timeDiff=-999999
            timeDiffResult="Fail-Time write not successful"            
    else: #If the initial time read fails
        print("The initial time read was not successful\n")
        timeDiff=-999999
        timeDiffResult="Fail-Initial time read not successful"        

    return [RTCVoltageRangeResult,RTCVoltageValueResult,timeDiffResult,timeDiff]

#Test SD Card is working
def testSDCard(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)==False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the SD Card Status
    [statusValue,statusResult]=checkStatus(x2,mbRetries,"SDTest","SD card")

    return statusResult

#Test that the system current is reading correctly
def testSysCur(GPIO,pinDict,x2,mbRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read system current
    print("Reading the system current...")
    readResult = mbReadRetries(x2,Reg.mbReg["SysCur"][0],Reg.mbReg["SysCur"][1],retries=mbRetries)
    if(readResult):
        curr=combineFrom16Bits(readResult)
        currentLevel=valueRangeCheck(150,10,curr)
    else:
        print("The read was not successful")
        return ["Fail-The Modbus read failed",-999999]

    return [currentLevel[1],curr]

#Test the Wi-Fi module is operating correctly
def testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries):
    powerOn(GPIO,pinDict,"IO1")
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")

    #NEED TO TURN ON WIFI SWITCH

    searchString=wifiNetwork
    retries=wifiRetries
    sleepSec = 2

    for i in range(0,retries):
        ssids=[cell.ssid for cell in Cell.all('wlan0')]
        print("List of all networks found:",ssids)
        for ssid in ssids:
            if (searchString in ssid):
                done=True
                print("Attempt", i+1, "of", retries, "was successful")
                print("Found network:",ssid)
                break
            else:
                done=False
        if(done):
            return ["Pass"]
        else:
            print("Failed to find a network with", searchString, "in it on attempt", i+1, "of", retries)
            if(i+1<retries):
                print("Waiting", sleepSec, "seconds and retrying...")
                time.sleep(sleepSec)
            else:
                print("Failed to find X2 network")
                return ["Fail-Network not found"]

#This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')
            

if __name__ == "__main__":
    main()
        
