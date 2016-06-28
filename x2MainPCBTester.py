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
import os
##import spidev
import x2mbRegisters as Reg
##import minimalmodbus
##import RPi.GPIO as GPIO

def main():

##        ##Open SPI bus for use by the ADC chip
##        spi = spidev.SpiDev()
##        spi.open(0,0)
##
##        ##Setup the modbus instance of the X2
##        x2 = minimalmodbus.Instrument(comPort, x2mbAddress)#Define the minimalmodbus instance mb
##        minimalmodbus.BAUDRATE= baud
##        minimalmodbus.PARITY=parity
##        minimalmodbus.BYTESIZE=bytesize
##        minimalmodbus.STOPBITS=stopbits
##        minimalmodbus.TIMEOUT=modbusTimeout
##        minimalmodbus._checkSlaveaddress = _checkSlaveaddress #call this function to adjust the modbus address range to 0-255

##        ##Define GPIO Interface
##        GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
##        #Define the pin numbers in a dictionary to allow easy reference
##        pin = {"IO1"       :   11,
##               "IO2"       :   13,
##               "IO3"       :   15,
##               "IO4"       :   12,
##               "TRIGGER1"  :   16,
##               "TRIGGER2"  :   18
##               }
##        #Set the GPIO directions
##        GPIO.setup(pin["IO1"], GPIO.OUT)
##        GPIO.setup(pin["IO2"], GPIO.OUT)
##        GPIO.setup(pin["IO3"], GPIO.OUT)
##        GPIO.setup(pin["IO4"], GPIO.OUT)
##        GPIO.setup(pin["TRIGGER1"], GPIO.OUT)
##        GPIO.setup(pin["TRIGGER2"], GPIO.OUT)
    

    ##Define program variables
    #Device Parameters
    snlen = 4 #length of the serial number
##        #USB RS-485 Parameters
##        x2mbAddress = 252
##        baud = 19200
##        parity = 'N'
##        bytesize=8
##        stopbits=1
##        modbusTimeout=0.1
##        comPort = '/dev/ttyUSB0'


    ##Create a file for tracking test results
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


    ##Continually loop through the test process to allow the user to test a batch of PCBs
    sn = getSN(snlen)
    while (sn != "-1"): #Loop through all PCBs to be tested
        out_records.write("%s" % sn) #Write serial number to file

        result=test3VLDO() #Call the 3V LDO test module
        out_records.write(",%s,%s" % (result[0],result[1])) #Write the result to the file
        
        result=testProcAndRS485() #Call the Processor and RS-485 test module
        out_records.write(",%s" % (result[0])) #Write the result to the file


        out_records.write("\n")#Line return to go to next record
        sn = getSN(snlen)

    out_records.close #close the file

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

def power0on(): #Checks if the Primary power is off and if so turns it on
    #if(IO1==OFF):
        #IO1 = ON
        #time.sleep(1)
    return True

##def readAnalog(ch): #ch must be 0-7
##    adc = spi.xfer2([1,(8+ch)<<4,0]) #Read from MCP3008 chip
##    data = ((adc[1]&3) << 8) + adc[2] #Convert to value
##
##    volts = (data*3.3)/float(1023) #Convert to voltage
##    volts = round(volts,2)#Rounds to two decimal places
##
##    return volts

def test3VLDO(): #Tests the 3V LDO is functioning correctly
    power0on()
    analog0 = 3.02 #readAnalog(0) #Read SPI0 ch. 0

    #Check if voltage is in range and return the result
    if (analog0 > 2.95):
        if (analog0 < 3.05):
            return ["Pass",analog0]
        else:
            return ["Fail-Voltage high",analog0]
    else:
        return ["Fail-Voltage low",analog0]

def testProcAndRS485():
    power0on()
##    x2.read_registers((Reg.mbReg["Add"][0]),(Reg.mbReg["Add"][1]))
    return ["Pass"]
    

###This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
##def _checkSlaveaddress(slaveaddress):
##    SLAVEADDRESS_MAX=255
##    SLAVEADDRESS_MIN=0
##    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')
            

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("User cancelled with Keyboard")
##        GPIO.cleanup()
    except Exception:
        print("An error occured")
##        GPIO.cleanup()
        
