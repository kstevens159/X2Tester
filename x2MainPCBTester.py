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
##        wifiNetwork = "X2 Logger"
        wifiNetwork = "ZyXEL"
        #USB RS-485 Parameters
        x2mbAddress = 252 #X2 Main universal address
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
        x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance
        x2.serial.baudrate = baud
        x2.serial.parity = parity
        x2.serial.bytesize = bytesize
        x2.serial.stopbits = stopbits
        x2.serial.timeout = modbusTimeout
        minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255
##        x2.debug=True

        ##Define GPIO Interface
        GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
        GPIO.setwarnings(False)
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

        #Check if folder is there and if not make
        os.makedirs("/home/pi/Documents/X2_PCB_Test_Results",exist_ok=True)
        #Define the file name to be <CURRENT_DATE>_PCBTestResults.csv
        name = "PCBTestResults.txt"
        date = datetime.datetime.now().strftime("%Y.%m.%d")
##    filename = os.path.dirname(__file__)+relativePath+date+"_"+name
        filename="/home/pi/Documents/X2_PCB_Test_Results/"+date+"_"+name

        #Open the file
        
        if(os.path.isfile(filename)):   #If the file exists append it
            out_records=open(filename, 'a')
        else:                           #If the file doesn't exist create it and add section headers
            out_records=open(filename, 'w')
            out_records.write("Serial Number,"
                              "3V LDO Status,"
                              "3V LDO Voltage,"
                              "Processor & Host RS-485 Status,"
                              "EE Chip Status,"
                              "RTC Battery Read Status,"
                              "RTC Battery Read Voltage,"
                              "RTC Clock Retention Status,"
                              "RTC Clock Retention Difference,"                              
                              "3.3V SEPIC Status,"
                              "3.3V SEPIC Voltage,"
                              "Serial Flash Status,"
                              "SD Card Status,"
                              "Primary Power Switch Status,"
                              "System Current Status,"
                              "System Current Value,"
                              "12V SEPIC Status,"
                              "5V LDO Status,"
                              "5V LDO Voltage,"
                              "12V Sensor Power Switch A Status,"
                              "12V Sensor Power Switch A Voltage,"
                              "12V Sensor Power Switch B Status,"
                              "12V Sensor Power Switch B Voltage,"
                              "12V Sensor Power Switch C Status,"
                              "12V Sensor Power Switch C Voltage,"
                              "12V Sensor Power Switch D Status,"
                              "12V Sensor Power Switch D Voltage,"
                              "12V Sensor Current Status,"
                              "12V Sensor Current Value,"
                              "Priority Power Output 1 Status,"
                              "Priority Power Output 1 Voltage,"
                              "Priority Power Output 2 Status,"
                              "Priority Power Output 2 Voltage,"
                              "Wi-Fi Network Status,"
                              "Wi-Fi Communication Status,"                               
                              "RS-485 Sensor A,"
                              "RS-485 Sensor B,"
                              "RS-485 Sensor C,"
                              "RS-232 Sensor A,"
                              "RS-232 Sensor B,"
                              "RS-232 Sensor C,"
                              "SDI-12 Sensor A,"
                              "SDI-12 Sensor B,"
                              "SDI-12 Sensor C,"
                              "Magnetic Switch Status,"
                              "Pressure/Temp/Humidity Chip Status,"
                              "Passthrough RS-485 Status,"
                              "Trigger 1 Status,"
                              "Trigger 2 Status,"
                              "\n")


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
            result1=test3VLDO(GPIO,pin,spi) #Call the 3V LDO test module
            print ("=====================")
            print("Test result:",result1)
            out_records.write(",%s,%s" % (result1[0],result1[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the RS-485 driver, EE and processor
            print("\n------------------------------")
            print("Testing the Processor & RS-485 Modbus Communication...")
            result2=testProcEEAndRS485(GPIO,pin,x2,mbRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result2)
            out_records.write(",%s,%s" % (result2[0],result2[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the RTC Clock & Battery
            print("\n------------------------------")
            print("Testing the RTC Clock...")
            result3=testRTC(GPIO,pin,x2,mbRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result3)
            out_records.write(",%s,%s,%s,%s" % (result3[0],result3[1],result3[2],result3[3])) #Write the result to the file
            print("------------------------------\n")

            #Test the 3.3V SEPIC Converter
            print("\n------------------------------")
            print("Testing the 3.3V SEPIC Converter...")
            result4=test33SEPIC(GPIO,pin,x2,mbRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result4)
            out_records.write(",%s,%s" % (result4[0],result4[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the Serial Flash
            print("\n------------------------------")
            print("Testing the Serial Flash...")
##            result5=testSerialFlash(GPIO,pin,x2,mbRetries) #Call the Processor and RS-485 test module
            print ("=====================")
##            print("Test result:",result5)
            print("Serial Flash test skipped")
##            out_records.write(",%s,%s" % (result5[0])) #Write the result to the file
            out_records.write(",Not tested")
            print("------------------------------\n")

            

            #Test the Wi-Fi module
            print("\n------------------------------")
            print("Testing the Wi-Fi Module...")
            result999=testWifi(GPIO,pin,x2,mbRetries,wifiNetwork,wifiRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result999)
            out_records.write(",%s" % (result999[0])) #Write the result to the file
            print("------------------------------\n")




            #Turn off the power
            GPIO.output(pin["IO1"],GPIO.LOW)
            GPIO.output(pin["IO2"],GPIO.LOW)
            GPIO.output(pin["IO3"],GPIO.LOW)
            GPIO.output(pin["IO4"],GPIO.LOW)

            input("The current board has finished testing and is safe to remove.\n"
                  "Press Enter to continue")
            print("----------------------------------------------")
            print("Board SN:",sn,"Done")
            print("----------------------------------------------\n\n")

            #Prepare for next board
            out_records.write("\n")#Line return to go to next record
            out_records.flush()
            sn = getSN(snlen) #Get new board SN

        #close the file
        out_records.close

        #Clean up GPIOs
        GPIO.cleanup()

    except KeyboardInterrupt:
        out_records.write(",PROGRAM ERROR\n")#Line return to go to next record
        out_records.close #Close the file
        GPIO.output(pin["IO1"],GPIO.LOW) #Turn power off to Primary Power
        GPIO.output(pin["IO2"],GPIO.LOW) #Turn power off to Secondary Power
        GPIO.output(pin["IO3"],GPIO.LOW) #Turn power off to Backup Power
        GPIO.output(pin["IO4"],GPIO.LOW) #Turn power off to T-Node
        GPIO.cleanup() #Clean up GPIOs
        print("\n==============================\n")
        print("The program encountered an error!\n")
        print("==============================\n")
        input("Press Enter to exit")
    except:
        out_records.write(",PROGRAM ERROR\n")#Line return to go to next record
        out_records.close #Close the file
        GPIO.output(pin["IO1"],GPIO.LOW) #Turn power off to Primary Power
        GPIO.output(pin["IO2"],GPIO.LOW) #Turn power off to Secondary Power
        GPIO.output(pin["IO3"],GPIO.LOW) #Turn power off to Backup Power
        GPIO.output(pin["IO4"],GPIO.LOW) #Turn power off to T-Node
        GPIO.cleanup() #Clean up GPIOs
        print("\n==============================\n")
        print("The program encountered an error!\n")
        print("==============================\n")
        input("Press Enter to exit")


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

#Used to get the PCB's serial number and ensure it is valid
def getSN(snlen):
    #Get the SN from the user
    sn = input("Please connect PCB and then enter the PCB's serial number (-1 if done): ")

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
def power0off(GPIO,pin):
    if(GPIO.input(pin["IO1"])== 1):
        GPIO.output(pin["IO1"],GPIO.LOW)
    return True

#Used to check the current status of the PCB's power and enable
#power if it is off
def power0on(GPIO,pin):
    if(GPIO.input(pin["IO1"])== 0):
        GPIO.output(pin["IO1"],GPIO.HIGH)
        #The sleep time of 1 works in IDLE, but not in the cmd line
        #Not sure reason, but possible execution speed is faster in cmd line
        time.sleep(2)
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


#-----------------------------------#

#Test the 3.3V SEPIC
def test33SEPIC(GPIO,pin,x2,mbRetries):
    power0on(GPIO,pin)
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing 3.3V SEPIC...\n")

    #Enable the 3.3V SEPIC
    print("Enabling the 3.3V SEPIC...")
    writeResult = mbWriteRetries(x2,Reg.mbReg["33SEPIC_OF"][0],[1],retries=mbRetries) #0=off; 1=on
    if(writeResult):
        print("The 3.3V SEPIC was successfully enabled")
    else:
        print("Enabling the 3.3V SEPIC was not successful")
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the 3.3V SEPIC voltage
    print("Reading 3.3V SEPIC Voltage...")
    readResult = mbReadRetries(x2,Reg.mbReg["VCC33_V"][0],Reg.mbReg["VCC33_V"][1],retries=mbRetries)
    if(readResult):
        print("The 3.3V SEPIC voltage level is",readResult[0],"\n")
    else:
        print("The 3.3V SEPIC voltage read was not successful\n")
        return ["Fail-Reading the 3.3V SEPIC voltage was not successful",-999999]

    #Check if voltage is in range and return the result
    vLevel=3.3 #expected voltage output
    vThreshold=0.1 #tolerance on the voltage check
    vRead=readResult[0] #read voltage level
    
    print("Checking voltage is in range...")
    if (vRead > vLevel-vThreshold):
        if (vRead < vLevel+vThreshold):
            print("Voltage is in range. It is",vRead)
            return ["Pass",vRead]
        else:
            print("Voltage is too high. It is",vRead)
            return ["Fail-Voltage high",vRead]
    else:
        print("Voltage is too low. It is",vRead)
        return ["Fail-Voltage low",vRead]

#Test the 3V LDO is functioning correctly
def test3VLDO(GPIO,pin,spi):   
    power0on(GPIO,pin)
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    print ("Testing 3V LDO...\n")

    print("Reading 3V LDO Voltage...")
    analog0 = readAnalog(spi,0) #Read SPI0 ch. 0
    print("The read voltage is",analog0,"\n")

    #Check if voltage is in range and return the result
    vLevel=3 #expected voltage output
    vThreshold=0.05 #tolerance on the voltage check
    vRead=analog0
    
    print("Checking voltage is in range...")
    if (vRead > vLevel-vThreshold):
        if (vRead < vLevel+vThreshold):
            print("Voltage is in range. It is",vRead)
            return ["Pass",analog0]
        else:
            print("Voltage is too high. It is",vRead)
            return ["Fail-Voltage high",vRead]
    else:
        print("Voltage is too low. It is",vRead)
        return ["Fail-Voltage low",vRead]


#Test that the RS-485 and processor are functioning correctly
def testProcEEAndRS485(GPIO,pin,x2,mbRetries):
    power0on(GPIO,pin)
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
        print("Power cycling to confirm EE works...")
        power0off(GPIO,pin)
        print("Power off. Waiting 1 second")
        time.sleep(1)
        power0on(GPIO,pin)
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
def testRTC(GPIO,pin,x2,mbRetries):
    power0on(GPIO,pin)
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
  
    #Read the RTC Voltage
    print("Reading the RTC Voltage...")
    RTCVoltageReadResult = mbReadRetries(x2,Reg.mbReg["RTCBAT"][0],Reg.mbReg["RTCBAT"][1],retries=mbRetries)
    if(RTCVoltageReadResult):
        print("The RTC Battery voltage is",RTCVoltageReadResult[0],"\n")
        if(RTCVoltageReadResult[0]>2.8 and RTCVoltageReadResult[0]<3.2):
            RTCVoltageResult="Pass"
        else:
            RTCVoltageResult="Fail-Voltage out of range"
    else:
        print("The RTC Battery voltage read was not successful\n")
        RTCVoltageReadResult=-999999
        RTCVoltageResult="Fail-Voltage read not successful"

    #Read the current time
    print("Reading Time from X2...")
    initialTimeReadResult = mbReadRetries(x2,0x701C,4) #Read from the X2
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
        tzOffset=0x0000 # Set the time zone offset to 0 for UTC time
        writeResult = mbWriteRetries(x2,0x701C,[timeIn16bit[0],timeIn16bit[1],0,0]) #Write to X2
        if(writeResult):
            print("Writing current computer time to X2 was successful\n")

            #Check if the board keeps time on a power cycle
            print("Cycling Power to board...")
            power0off(GPIO,pin)
            print("Waiting 1 seconds...")
            time.sleep(1)
            print("Turning board back on and checking time is accurate\n")
            power0on(GPIO,pin)

            #Read the boards current time
            print("Reading Time from X2...")
            finalTimeReadResult = mbReadRetries(x2,0x701C,4) #Read from the X2
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

    return [RTCVoltageResult,RTCVoltageReadResult[0],timeDiffResult,timeDiff]

#Test the Wi-Fi module is operating correctly
def testWifi(GPIO,pin,x2,mbRetries,wifiNetwork,wifiRetries):
    power0on(GPIO,pin)
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
        
