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

##import sys
##print(sys.path, "\n")
##sys.path.insert(0,"/usr/bin")
##print(sys.path, "\n")
##print("Minimal Modbus location",minimalmodbus.__file__)

def main():

    ##############################
    ## Define program variables ##
    ##############################
    
    #Device Parameters
    snlen = 4 #length of the serial number
    mbRetries = 3 #Number of retries on modbus commands
    wifiRetries = 25
##    wifiNetwork = "X2 Logger"
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
##    x2.debug=True

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
                          "Wi-Fi Network Status,"
                          "Wi-Fi Communication Status,"                          
                          "RTU Battery Status,"
                          "RTU Battery Voltage,"
                          "3.3V SEPIC Status,"
                          "3.3V SEPIC Voltage,"
                          "EE Status,"
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
        result=test3VLDO(GPIO,pin,spi) #Call the 3V LDO test module
        print("Test result:",result)
        out_records.write(",%s,%s" % (result[0],result[1])) #Write the result to the file
        print("------------------------------\n")

        #Test the RS-485 driver and processor
        print("\n------------------------------")
        print("Testing the Processor & RS-485 Modbus Communication...")
        result=testProcAndRS485(GPIO,pin,x2,mbRetries) #Call the Processor and RS-485 test module
        print("Test result:",result)
        out_records.write(",%s" % (result[0])) #Write the result to the file
        print("------------------------------\n")

        #Test the Wi-Fi module
        print("\n------------------------------")
        print("Testing the Wi-Fi Module...")
        result=testWifi(x2,mbRetries,wifiNetwork,wifiRetries) #Call the Processor and RS-485 test module
        print("Test result:",result)
        out_records.write(",%s" % (result[0])) #Write the result to the file
        print("------------------------------\n")


        #Turn off the board
        GPIO.output(pin["IO1"],GPIO.LOW)

        input("The current board has finished testing and is safe to remove.\n"
              "Press Enter to continue")

        #Prepare for next board
        out_records.write("\n")#Line return to go to next record
        out_records.flush()
        sn = getSN(snlen) #Get new board SN

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

#This function is used to gracefully handle failed writes and allow retries 
def mbWriteRetries(device,reg,value,retries=5):
    for i in range (0,retries):
        try:
            device.serial.flushInput() #clear serial buffer before writing
            result=device.write_registers(reg,value)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value

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


#Tests the 3V LDO is functioning correctly
def test3VLDO(GPIO,pin,spi):
    power0on(GPIO,pin)
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
def testProcAndRS485(GPIO,pin,x2,mbRetries):
    power0on(GPIO,pin)
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

#Test the Wi-Fi modules is operating correctly
def testWifi(x2,mbRetries,wifiNetwork,wifiRetries):
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
                print("Failed to find network")
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
        GPIO.output(pin["IO1"],GPIO.LOW)
        GPIO.cleanup()
    except:
        print("An error occured")
        GPIO.output(pin["IO1"],GPIO.LOW)
        GPIO.cleanup()
        
