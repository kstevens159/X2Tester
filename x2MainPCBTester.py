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
        wifiNetwork = "X2 Logger-C899CF"
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
##        x2.debug=True

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
        
        ########################
        ## Create Output File ##
        ########################

        #Check if folder is there and if not make
        os.makedirs("/home/pi/Documents/X2_PCB_Test_Results",exist_ok=True)
        #Define the file name to be <CURRENT_DATE>_PCBTestResults.csv
        name = "PCBTestResults.csv"
        date = datetime.datetime.now().strftime("%Y.%m.%d")
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
                              "Backup Power Switch Status,"
                              "Backup Power Voltage,"
                              "Backup Valid,"
                              "Secondary Power Switch Status,"
                              "Secondary Power Voltage,"
                              "Secondary Valid,"
                              "Primary Power Switch Status,"
                              "Primary Power Voltage,"
                              "Primary Valid,"
                              "PPP_1DISCON Status,"
                              "PPP_1DISCON Valid,"
                              "System Current Status,"
                              "System Current Value,"
                              "12V SEPIC Status,"
                              "12V SEPIC Voltage,"
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
                              "wi-Fi LED and Communication Status,"
                              "Port 0 RS-485 Sensor Status,"
                              "Port 0 RS-232 Sensor Status,"
                              "Port 0 SDI-12 Sensor Status,"
                              "Port 1 RS-485 Sensor Status,"
                              "Port 1 RS-232 Sensor Status,"
                              "Port 1 SDI-12 Sensor Status,"
                              "Port 2 RS-485 Sensor Status,"
                              "Port 2 RS-232 Sensor Status,"
                              "Port 2 SDI-12 Sensor Status,"                              
                              "Magnetic Switch Status,"
                              "Pressure/Temp/Humidity Chip Status,"
                              "Passthrough RS-485 Status,"
                              "Trigger 1 Status,"
                              "Trigger 2 Status,"
                              "Itteration Time,"
                              "\n")


        ###################
        ## PCB Test Loop ##
        ###################

        ##Continually loop through the test process to allow the user to test a batch of PCBs
        sn = getSN(snlen)
        while (sn != "-1"): #Loop through all PCBs to be tested
            startTime=time.time()#Timestamp beginning time
            
            out_records.write("%s" % sn) #Write serial number to file

            #Test the 3V LDO
            print("\n------------------------------")
            print("Testing the 3V LDO...")
            result1=test3VLDO(GPIO,pinDict,x2,mbRetries,spi) #Call the 3V LDO test module
            print ("=====================")
            print("Test result:",result1)
            out_records.write(",%s,%s" % (result1[0],result1[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the RS-485 driver, EE and processor
            print("\n------------------------------")
            print("Testing the Processor & RS-485 Modbus Communication...")
            result2=testProcEEAndRS485(GPIO,pinDict,x2,mbRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result2)
            out_records.write(",%s,%s" % (result2[0],result2[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the RTC Clock & Battery
            print("\n------------------------------")
            print("Testing the RTC Clock...")
            result3=testRTC(GPIO,pinDict,x2,mbRetries) #Call the RTC Test module
            print ("=====================")
            print("Test result:",result3)
            out_records.write(",%s,%s,%s,%s" % (result3[0],result3[1],result3[2],result3[3])) #Write the result to the file
            print("------------------------------\n")

            #Test the 3.3V SEPIC Converter
            print("\n------------------------------")
            print("Testing the 3.3V SEPIC Converter...")
            result4=test33SEPIC(GPIO,pinDict,x2,mbRetries) #Call the 3.3V SEPIC test module
            print ("=====================")
            print("Test result:",result4)
            out_records.write(",%s,%s" % (result4[0],result4[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the Serial Flash
            print("\n------------------------------")
            print("Testing the Serial Flash...")
##            result5=testSerialFlash(GPIO,pinDict,x2,mbRetries) #Call the serial flash test module
            print ("=====================")
##            print("Test result:",result5)
            print("Serial Flash test skipped")
##            out_records.write(",%s,%s" % (result5[0])) #Write the result to the file
            out_records.write(",Not tested")
            print("------------------------------\n")

            #Test SD Card
            print("\n------------------------------")
            print("Testing the SD Card...")
            result6=testSDCard(GPIO,pinDict,x2,mbRetries) #Call the SD Card test module
            print ("=====================")
            print("Test result:",result6)
            out_records.write(",%s" % (result6[0])) #Write the result to the file
            print("------------------------------\n")

            #Test Priority Power Switch
            print("\n------------------------------")
            print("Testing the Priority Power Switch...")
            result7=testPrioPwrPathSW(GPIO,pinDict,x2,mbRetries) #Call the PPSW test module
            print ("=====================")
            print("Test result:",result7)
            out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (result7[0],result7[1],bin(result7[2]), #Write the results to the file
                                                                     result7[3],result7[4],bin(result7[5]),
                                                                     result7[6],result7[7],bin(result7[8]),
                                                                     result7[9],bin(result7[10])))
            print("------------------------------\n")
            
            #Test System Current
            print("\n------------------------------")
            print("Testing the System Current...")
            result8=testSysCur(GPIO,pinDict,x2,mbRetries) #Call the system current test module
            print ("=====================")
            print("Test result:",result8)
            out_records.write(",%s,%s" % (result8[0],result8[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the 12V SEPIC Converter
            print("\n------------------------------")
            print("Testing the 12V SEPIC Converter...")
            result9=test12SEPIC(GPIO,pinDict,x2,mbRetries) #Call the 12V SEPIC test module
            print ("=====================")
            print("Test result:",result9)
            out_records.write(",%s,%s" % (result9[0],result9[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the 5V LDO Converter
            print("\n------------------------------")
            print("Testing the 5V LDO Converter...")
            result10=test5VLDO(GPIO,pinDict,x2,mbRetries,spi) #Call the 5V LDO test module
            print ("=====================")
            print("Test result:",result10)
            out_records.write(",%s,%s" % (result10[0],result10[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the 12V Sensor Switch
            print("\n------------------------------")
            print("Testing the 12V Sensor Switch...")
            result11=test12VSenSW(GPIO,pinDict,x2,mbRetries,spi) #Call the 12V Sensor Switch test module
            print ("=====================")
            print("Test result:",result11)
            out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s" % (result11[0],result11[1], #Write the results to the file
                                                            result11[2],result11[3],
                                                            result11[4],result11[5],
                                                            result11[6],result11[7]))
            print("------------------------------\n")

            #Test Sensor Current
            print("\n------------------------------")
            print("Testing the Sensor Current...")
            result12=testSenCur(GPIO,pinDict,x2,mbRetries) #Call the system current test module
            print ("=====================")
            print("Test result:",result12)
            out_records.write(",%s,%s" % (result12[0],result12[1])) #Write the result to the file
            print("------------------------------\n")

            #Test Priority Power Out Switch
            print("\n------------------------------")
            print("Testing the Priority Power Out Switch...")
            result13=testPrioPwrOutSW(GPIO,pinDict,x2,mbRetries,spi) #Call the priority power out switch test module
            print ("=====================")
            print("Test result:",result13)
            out_records.write(",%s,%s,%s,%s" % (result13[0],result13[1],
                                                result13[2],result13[3])) #Write the result to the file
            print("------------------------------\n")

            #Test the Wi-Fi module (LEDs, Communication, Network)
            print("\n------------------------------")
            print("Testing the Wi-Fi Module...")
            result14=testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries) #Call the Processor and RS-485 test module
            print ("=====================")
            print("Test result:",result14)
            out_records.write(",%s,%s" % (result14[0],result14[1])) #Write the result to the file
            print("------------------------------\n")

            #Test the Sensor Ports
            print("\n------------------------------")
            print("Testing the Sensor Ports...")
            result15=testSensor(GPIO,pinDict,x2,mbRetries,modbusTimeout) #Call the Sensor port test module
            print ("=====================")
            print("Test result:",result15)
            out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s,%s" % (result15[0],result15[1],result15[2],
                                                               result15[3],result15[4],result15[5],
                                                               result15[6],result15[7],result15[8],)) #Write the result to the file
            print("------------------------------\n")


            












            

            #Mark end of board itteration
            endTime=time.time()#Timestamp ending time
            itterationTime=round(endTime-startTime,1)
            out_records.write(",%s" % (itterationTime))

            #Turn off the power
            GPIO.output(pinDict["IO1"],GPIO.LOW)
            GPIO.output(pinDict["IO2"],GPIO.LOW)
            GPIO.output(pinDict["IO3"],GPIO.LOW)
            GPIO.output(pinDict["IO4"],GPIO.LOW)
            
            input("The current board has finished testing and is safe to remove.\n"
                  "Please remember to remove the SD Card\n\n"
                  "Press Enter to continue\n")
            print("----------------------------------------------")
            print("Board SN:",sn,"Done")
            print("The test took a total of",itterationTime,"seconds")
            print("----------------------------------------------\n\n")

            #Prepare for next board
            out_records.write("\n")#Line return to go to next record
            out_records.flush()
            sn = getSN(snlen) #Get new board SN

    #Define operation when an exception occurs
    except KeyboardInterrupt:
        out_records.write(",KEYBOARD INTERRUPT ERROR\n")#Line return to go to next record
        out_records.flush()        
        print("\n==============================\n")
        print("The program was cancelled by a keyboard interrupt!\n")
        print("==============================\n")
        input("Press Enter to exit\n")
    except Exception as error:
        out_records.write(",PROGRAM ERROR,")
        out_records.write(str(error))
        out_records.write("\n")#Line return to go to next record
        out_records.flush()
        print("\n==============================\n")
        print("The program encountered the following error!\n")
        print("Error Type: ", type(error))
        print(error.args)
        print(error)
        print("==============================\n")
        input("Press Enter to exit\n")
    finally:
        print("Cleaning up and exiting...")
        out_records.close #Close the file
        GPIO.output(pinDict["IO1"],GPIO.LOW) #Turn power off to Primary Power
        GPIO.output(pinDict["IO2"],GPIO.LOW) #Turn power off to Secondary Power
        GPIO.output(pinDict["IO3"],GPIO.LOW) #Turn power off to Backup Power
        GPIO.output(pinDict["IO4"],GPIO.LOW) #Turn power off to T-Node
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
##    return 1234 #Use during testing to avoid needing to enter SN each time
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
def mbReadFloatRetries(device,reg,numReg=2,retries=5): #(Minimalmodbus device),(Register address),(Number of registers to read),(Retry attempts)
    for i in range (0,retries):
        try:
            device.serial.flushInput() #clear serial buffer before reading
            result=device.read_float(reg,functioncode=4,numberOfRegisters=numReg)
            result=round(result,3)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            print("Reading",i,"Failed")
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return [result]
#Returns False if it fails and the read values if successful

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
            print("Writing",i,"Failed")
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value
#Returns False if it fails and the values that were written if successful

#Used to check the current status of the PCB's power and disable
#power if it is on
def powerOff(GPIO,pinDict,pinValue,delay=5):
    print("Powering",pinValue,"off...")
    if(GPIO.input(pinDict[pinValue])== 1):
        GPIO.output(pinDict[pinValue],GPIO.LOW)
        time.sleep(delay)
    return True

#Used to check the current status of the PCB's power and enable
#power if it is off
def powerOn(x2,mbRetries,GPIO,pinDict,pinValue,delay=3):
    print("Powering",pinValue,"on...")
    if(GPIO.input(pinDict[pinValue])== 0):
        GPIO.output(pinDict[pinValue],GPIO.HIGH)
        #The sleep time of 1 works in IDLE, but not in the cmd line
        #Not sure reason, but possible execution speed is faster in cmd line
        time.sleep(delay)

        #Turn off the Wi-Fi so it doesn't interfere on the RS-485 bus
        enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)
    return True

#Tests the voltage and valid line status for a power input channel
def prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,mbDictName,validCheck,validValue):
    #Read the Channel Voltage
    print("Reading Channel Voltage...")
    readResult1 = mbReadFloatRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries)
    if(readResult1):
        chVoltage=readResult1[0]
        print("The channel voltage level is",chVoltage,"\n")
        
        #Check if voltage is in range
        rangeCheck=valueRangeCheck(12.0,2,chVoltage)#Expected, tolerance, test input
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
            print("The valid lines read",bin(readResult2[0]))
            if(readResult2[0]== validValue): #If read was successful check the correct lines are enabled
                print("The correct valid lines were enabled\n")
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

    scaledVolts = volts*scale
    scaledVolts = round(scaledVolts,3)

    return scaledVolts

#Calculate voltage divider scaling value
#This gives the value to multiply by 3.3 to get actual voltage
def scaleValue(R1,R2):
    return ((R1+R2)/R2)

#Test each sensor port
def sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,mbDictName,clearText,spiCh):
    print("\n")
    #Enable 12V SW
    if(enableDisable(x2,mbRetries,mbDictName,clearText,1)):
        #If successfully enabled check the output voltage
        print("Reading 12V",clearText,"Voltage...")
        scaling=scaleValue(27.4,10)
        analog = readAnalog(spi,spiCh,scaling) #Read SPI0 ch. 1
        print("The read voltage is",analog,"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(12,0.5,analog)#Expected, tolerance, test input

        return [rangeCheck[1],analog]
    else:
        return ["Fail-Unable to enable"+clearText,-999999]

def sensorTest(x2,mbRetries,RS232Channel):

    #Send RS-485 Command
    print("\nTesting RS-485 Communicaiton")
    [portValue485,portStatus485]=checkStatus(x2,mbRetries,"RS485ComTest","RS-485 Communication Test")

    #Send RS-232 Command
    print("\nTesting RS-232 Communicaiton")
    [portValue232,portStatus232]=checkStatus(x2,mbRetries,RS232Channel,"RS-232 Communication Test")

    #Send SDI-12 Command
    print("\nTesting SDI-12 Communicaiton")
    [portValueSDI12,portStatusSDI12]=checkStatus(x2,mbRetries,"SDI12ComTest","SDI-12 Communication Test")

    return [portStatus485,portStatus232,portStatusSDI12]

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


#Test the 12V SEPIC
def test12SEPIC(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Read the 12V SEPIC voltage
    print("Reading 12V SEPIC Voltage...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["12VSen_V"][0],Reg.mbReg["12VSen_V"][1],retries=mbRetries)
    if(readResult):
        print("The 12V SEPIC voltage level is",readResult[0],"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(12,0.5,readResult[0])#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off SEPIC
        return[rangeCheck[1],readResult[0]]
    else:
        print("The 12V SEPIC voltage read was not successful\n")
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off SEPIC
        return ["Fail-Reading the 12V SEPIC voltage was not successful",-999999]

#Test 12V Sensor Switch
def test12VSenSW(GPIO,pinDict,x2,mbRetries,spi):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    print("\n")
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999
                ]

    #Check switch port A
    [sensorAStatus,sensorAVLevel]= sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,"12V_A_OF","Port A",2)
    enableDisable(x2,mbRetries,"12V_A_OF","12V Sensor Port A",0)#Turn off after

    #Check switch port B
    [sensorBStatus,sensorBVLevel]= sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,"12V_B_OF","Port B",3)
    enableDisable(x2,mbRetries,"12V_B_OF","12V Sensor Port B",0)#Turn off after

    #Check switch port C
    [sensorCStatus,sensorCVLevel]= sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,"12V_C_OF","Port C",4)
    enableDisable(x2,mbRetries,"12V_C_OF","12V Sensor Port C",0)#Turn off after

    #Check switch port D
    [sensorDStatus,sensorDVLevel]= sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,"12V_D_OF","Port D",5)
    enableDisable(x2,mbRetries,"12V_D_OF","12V Sensor Port D",0)#Turn off after

    return [sensorAStatus,sensorAVLevel,
            sensorBStatus,sensorBVLevel,
            sensorCStatus,sensorCVLevel,
            sensorDStatus,sensorDVLevel
            ]
    
#Test the 3.3V SEPIC
def test33SEPIC(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    print("\n")
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1) == False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the 3.3V SEPIC voltage
    print("\nReading 3.3V SEPIC Voltage...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["VCC33_V"][0],Reg.mbReg["VCC33_V"][1],retries=mbRetries)
    if(readResult):
        print("The 3.3V SEPIC voltage level is",readResult[0],"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(3.3,0.1,readResult[0])#Expected, tolerance, test input

        return[rangeCheck[1],readResult[0]]
    else:
        print("The 3.3V SEPIC voltage read was not successful\n")
        return ["Fail-Reading the 3.3V SEPIC voltage was not successful",-999999]

#Test the 3V LDO is functioning correctly
def test3VLDO(GPIO,pinDict,x2,mbRetries,spi):   
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    print("\nReading 3V LDO Voltage...")
    analog0 = readAnalog(spi,0) #Read SPI0 ch. 0
    print("The read voltage is",analog0,"\n")

    #Check if voltage is in range and return the result
    rangeCheck=valueRangeCheck(3.0,0.05,analog0)#Expected, tolerance, test input

    return[rangeCheck[1],analog0]

#Test the 5V LDO is functioning correctly
def test5VLDO(GPIO,pinDict,x2,mbRetries,spi):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Enable 5V LDO
    print("\n")
    if(enableDisable(x2,mbRetries,"5VLDO_OF","5V LDO",1)):
        #If successfully enabled check the output voltage
        print("\nReading 5V LDO Voltage...")
        scaling=scaleValue(6.04,10)
        analog1 = readAnalog(spi,1,scaling) #Read SPI0 ch. 1
        print("The read voltage is",analog1,"\n")

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(5.0,0.1,analog1)#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"5VLDO_OF","5V LDO",0)#Turn off 5V LDO
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC

        return [rangeCheck[1],analog1]
    else:
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC
        return ["Fail-Enabling the 5V LDO was not successful",-999999]


#Test the priority power path out switch is working correctly
def testPrioPwrOutSW(GPIO,pinDict,x2,mbRetries,spi):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")


    #Enable Priority Power Out Switch
    print("\n")
    if(enableDisable(x2,mbRetries,"PriPwr_OF","Priority Power Out Switch",1)):
        #If successfully enabled check the output voltage
        print("\nReading Output Voltages...")
        scaling=scaleValue(82.5,10)#Voltage divider X factor
        analog6 = readAnalog(spi,6,scaling) #Read SPI0 ch. 6
        analog7 = readAnalog(spi,7,scaling) #Read SPI0 ch. 7
        print("The J7 board to board read voltage is",analog6)
        print("The J3 JST read voltage is",analog7,"\n")

        #Check if voltage is in range and return the result
        rangeCheck1=valueRangeCheck(12,0.5,analog6)#Expected, tolerance, test input
        rangeCheck2=valueRangeCheck(12,0.5,analog7)#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"PriPwr_OF","Priority Power Out Switch",0)#Turn off prio. pwr. out sw.

        return [rangeCheck1[1],analog6,
                rangeCheck2[1],analog7]       
    else:
        return ["Fail-Enabling priority power out switch was not successful",-999999,
                "Fail-Enabling priority power out switch was not successful",-999999]

#Test the priority power path switch is working correctly
def testPrioPwrPathSW(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO3",delay=3)#Enable the backup power input
    powerOff(GPIO,pinDict,"IO1",delay=0)#Ensure Primary input is off
    powerOff(GPIO,pinDict,"IO2",delay=0)#Ensure Secondary input is off

    #Enable 3.3V SEPIC and set a flag on whether to test the valid lines
    validCheck = enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)

    ##Test backup input
    print("\nTesting the Backup Input...\n")
    [bakStat,bakVoltage,bakValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"BakPwr_V",validCheck,0b100)

    ##Test secondary input
    powerOn(x2,mbRetries,GPIO,pinDict,"IO2",delay=1)#Enable secondary input
    
    print("\nTesting the Secondary Input...\n")
    [secStat,secVoltage,secValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"SecPwr_V",validCheck,0b110)

    ##Test primary input
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1",delay=1)#Enable primary input
    
    print("\nTesting the Primary Input...\n")
    [priStat,priVoltage,priValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"PriPwr_V",validCheck,0b111)

    ##Test PPP_1DISCON
    print("\nTriggering disconnect of Primary Power...\n")

    #Enabled the PPP_1DISCON pin to pull UV of Primary to GND
    writeResult1 = mbWriteRetries(x2,Reg.mbReg["PPP_Dis"][0],[1],retries=mbRetries)#0 (default) = pri on; 1 = pri off
    if(writeResult1):
        print("The primary power has been disabled")
        #Read the valid lines
        readResult = mbReadRetries(x2,Reg.mbReg["Valid"][0],Reg.mbReg["Valid"][1],retries=mbRetries)
        if(readResult):
            PPP_DisValid=readResult[0]
            print("The valid lines read",bin(PPP_DisValid))
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

        #Unset the Priority Power disconnect to prevent an unnecessary power cycle
        print("Re-enabling the primary power input...")
        writeResult2 = mbWriteRetries(x2,Reg.mbReg["PPP_Dis"][0],[0],retries=mbRetries)#0=pri on; 1=pri off
        if(writeResult2):
            time.sleep(1)#Pause to make sure it is back online before continuing
            print("The primary power has been enabled")
        else:
            print("Re-enabling the primary power failed")
    else:
        print("The write was not successful")
        PPP_DisStatus="Fail-Disabling primary power failed"
        PPP_DisValid=-999999
    
    #Disable secondary and backup inputs
    powerOff(GPIO,pinDict,"IO2",delay=0)
    powerOff(GPIO,pinDict,"IO3",delay=0)

    return [bakStat,bakVoltage,bakValid,secStat,secVoltage,secValid,priStat,priVoltage,priValid,PPP_DisStatus,PPP_DisValid]


#Test that the RS-485 and processor are functioning correctly
def testProcEEAndRS485(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Read the current address
    print("\nReading address...")
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
        print("Power off")
        powerOn(x2,mbRetries,GPIO,pinDict,"IO1")
        print("Power on\n")

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
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")
  
    #Read the RTC Voltage
    print("Reading the RTC Voltage...")
    RTCRawResult = mbReadFloatRetries(x2,Reg.mbReg["RTCBAT_V"][0],Reg.mbReg["RTCBAT_V"][1],retries=mbRetries)
    if(RTCRawResult):
        RTCVoltageValueResult = RTCRawResult[0]
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
            print("Turning board back on and checking time is accurate")
            powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

            #Read the boards current time
            print("\nReading Time from X2...")
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
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)==False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    print("\n")

    #Read the SD Card Status
    [statusValue,statusResult]=checkStatus(x2,mbRetries,"SDTest","SD card")

    return [statusResult]

#Test that the system current is reading correctly
def testSenCur(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Enable switch port A
    if(enableDisable(x2,mbRetries,"12V_A_OF","12V Port A",1)== False):
        return ["Fail-Enabling 12V Port A was not successful",-999999]

    #Read sensor current
    print("\nReading the sensor current...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["SenCur"][0],Reg.mbReg["SenCur"][1],retries=mbRetries)
    if(readResult):
        curr=readResult[0]
        currentLevel=valueRangeCheck(15,10,curr)
    else:
        print("The read was not successful")
        return ["Fail-The Modbus read failed",-999999]

    print("\n")
    enableDisable(x2,mbRetries,"12V_A_OF","12V Sensor Port A",0)#Turn off port A after
    enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC after

    return [currentLevel[1],curr]

#Test Sensor Ports
def testSensor(GPIO,pinDict,x2,mbRetries,modbusTimeout):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)==False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful"]

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful",
                "Fail-Enabling the 12V SEPIC was not successful"]

    #Set the Modbus timeout to 5 seconds during sensor testing so they have time to respond
    x2.serial.timeout = 3

    ##Test Port 0
    #Enable switch port A
    print("\n")
    if(enableDisable(x2,mbRetries,"12V_A_OF","12V Port 0",1)):
        print("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port0Status = sensorTest(x2,mbRetries,"RS232AComTest")
        enableDisable(x2,mbRetries,"12V_A_OF","12V Port 0",0)
    else:
        port0Status = ["Fail-Enabling 12V Port A was not successful",
                       "Fail-Enabling 12V Port A was not successful",
                       "Fail-Enabling 12V Port A was not successful"]

    ##Test Port 1
    #Enable switch port B
    print("\n")
    if(enableDisable(x2,mbRetries,"12V_B_OF","12V Port 1",1)):
        print("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port1Status = sensorTest(x2,mbRetries,"RS232BComTest")
        enableDisable(x2,mbRetries,"12V_B_OF","12V Port 1",0)
    else:
        port1Status = ["Fail-Enabling 12V Port 1 was not successful",
                       "Fail-Enabling 12V Port 1 was not successful",
                       "Fail-Enabling 12V Port 1 was not successful"]

    ##Test Port 2
    #Enable switch port C
    print("\n")
    if(enableDisable(x2,mbRetries,"12V_C_OF","12V Port 2",1)):
        print("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port2Status = sensorTest(x2,mbRetries,"RS232CComTest")
        enableDisable(x2,mbRetries,"12V_C_OF","12V Port 2",0)
    else:
        port2Status = ["Fail-Enabling 12V Port 2 was not successful",
                       "Fail-Enabling 12V Port 2 was not successful",
                       "Fail-Enabling 12V Port 2 was not successful"]


    #Set the Modbus timeout back to the program default
    x2.serial.timeout = modbusTimeout
    

    return [port0Status[0],port0Status[1],port0Status[2],
            port1Status[0],port1Status[1],port1Status[2],
            port2Status[0],port2Status[1],port2Status[2]]

#Test that the system current is reading correctly
def testSysCur(GPIO,pinDict,x2,mbRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read system current
    print("\nReading the system current...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["SysCur"][0],Reg.mbReg["SysCur"][1],retries=mbRetries)
    if(readResult):
        curr=readResult[0]
        currentLevel=valueRangeCheck(5,3,curr)
    else:
        print("The read was not successful")
        return ["Fail-The Modbus read failed",-999999]

    return [currentLevel[1],curr]

#Test the Wi-Fi module is operating correctly
def testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries):
    print ("=====================")
    print (datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S"))
    print ("=====================")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    print("\n")
    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful"]
    #Enable the Wi-Fi Module
    if(enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",1)== False):
        return ["Fail-Enabling the Wi-Fi Module was not successful",
                "Fail-Enabling the Wi-Fi Module was not successful"]

    time.sleep(8)
    
    #Search for Wi-Fi network name
    networkStatus=wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2)

    #Enable the Wi-Fi LEDs
    print("\nTesting the Wi-Fi LEDs...")
    [commStatusValue1,commStatus1]=checkStatus(x2,mbRetries,"WiFiComLEDTest","Wi-Fi LED Enable Write")
    #Check if LEDs were enabled
    done=False
    while not(done):
        LEDUserInput = input("Did all 4 Wi-Fi LEDs come on? (y/n): ")
        if(LEDUserInput == "y" or LEDUserInput == "Y"):
            print("\nSuccess - You indicated that the LEDs were enabled\n")
            LEDStatus = "Pass"
            done=True
        elif (LEDUserInput == "n" or LEDUserInput == "n"):
            print("\nFailure -  You indicated that the LEDs were not all enabled\n"
                  "This could mean no communication to Wi-Fi module or LEDs not connected correctly\n")
            LEDStatus = "Fail-All LEDs were not turned on"
            done=True
        else:
            print("\nYou must enter y or n. Try again.\n")
            done=False

    #Disable Wi-Fi Module
    enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)

    return [networkStatus,LEDStatus]

#Test if a read voltage falls in a certain range
def valueRangeCheck(level,threshold,read):
    #Expected value, tolerance, input to test
    
    print("Checking if reading is in range...")
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


def wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2):  
    print("Looking for an X2 Wi-Fi network...")
    for i in range(0,wifiRetries):
        ssids=[cell.ssid for cell in Cell.all('wlan0')]
        print("\nList of all networks found:",ssids,"\n")
        for ssid in ssids:
            if (wifiNetwork in ssid):
                done=True
                print("Attempt", i+1, "of", wifiRetries, "was successful")
                print("Found network:",ssid)
                break
            else:
                done=False
        if(done):
            print("Successfully found the Wi-Fi network\n")
            return "Pass"
        else:
            print("Failed to find a network with", wifiNetwork, "in it on attempt", i+1, "of", wifiRetries)
            if(i+1<wifiRetries):
                print("Waiting", sleepSec, "seconds and retrying...")
                time.sleep(sleepSec)
            else:
                print("Failed to find X2 network\n")
                return "Fail-Network not found"

#This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')
            

if __name__ == "__main__":
    main()
        
