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
#       on a Raspberry Pi 3 with Python 3.
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
import shutil
import logging
import logging.handlers

############################################
## Setup global settings for the log file ##
############################################

#Logging Settings
log_level_console = logging.INFO #For Tester Use
##log_level_console = logging.DEBUG #For NexSens Use
log_level_file = logging.DEBUG #Always capture all to the log

#Check if folder is there and if not make
os.makedirs("/home/pi/Documents/X2_PCB_Test_Results/Logs",exist_ok=True)
log_file_name = "/home/pi/Documents/X2_PCB_Test_Results/Logs/ProgramRun.log"

#Create the logger object
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)#Allows the handlers to get anything higher than this level

#Define the log formats
formatter_file=logging.Formatter('%(message)s [%(levelname)s]')
formatter_console=logging.Formatter('%(message)s')

#Create the handler for the file output
logger_file=logging.handlers.TimedRotatingFileHandler(log_file_name,when='D', interval = 1, backupCount=0) #Creates a new log file each day
logger_file.setLevel(log_level_file)
logger_file.setFormatter(formatter_file)
logger.addHandler(logger_file)

#Create the handler for the console output
logger_console=logging.StreamHandler()
logger_console.setLevel(log_level_console)
logger_console.setFormatter(formatter_console)
logger.addHandler(logger_console)


def main():
    try: #Put everything in a try statement to allow the capturing and handling of errors
        
        ##############################
        ## Define program variables ##
        ##############################
        
        #Device Parameters
        snlen = 4 #length of the serial number
        mbRetries = 3 #Number of retries on modbus commands
        wifiRetries = 3 #Number of times to search for a Wi-Fi network before giving up
        wifiNetwork = "X2 Logger" #Partial Wi-Fi SSID name for which to scan

        #USB RS-485 Parameters
        x2mbAddress = 252 #X2 Main universal address
        tnodembAddress = 20
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

        #Setup the modbus instance of the Passthrough T-Node
        tnode = minimalmodbus.Instrument(comPort, tnodembAddress)#Define the minimalmodbus instance
        tnode.serial.baudrate = baud
        tnode.serial.parity = parity
        tnode.serial.bytesize = bytesize
        tnode.serial.stopbits = stopbits
        tnode.serial.timeout = modbusTimeout
##        tnode.debug=True

        ##Define GPIO Interface
        GPIO.setmode(GPIO.BOARD) #Sets the pin mode to use the board's pin numbers
        GPIO.setwarnings(False) #supresses the error if pins are already setup
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
        GPIO.setup(pinDict["TRIGGER1"], GPIO.IN)
        GPIO.setup(pinDict["TRIGGER2"], GPIO.IN)

        
        #########################
        ## Create Results File ##
        #########################

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
                              "Port 0 RS-485 Sensor Status,"
                              "Port 0 RS-232 Sensor Status,"
                              "Port 0 SDI-12 Sensor Status,"
                              "Port 1 RS-485 Sensor Status,"
                              "Port 1 RS-232 Sensor Status,"
                              "Port 1 SDI-12 Sensor Status,"
                              "Port 2 RS-485 Sensor Status,"
                              "Port 2 RS-232 Sensor Status,"
                              "Port 2 SDI-12 Sensor Status,"                              
                              "Pressure/Temp/Humidity Chip Status,"
                              "Pressure Status,"
                              "Pressure Reading,"
                              "Temperature Status,"
                              "Temperature Reading,"
                              "Humidity Status,"
                              "Humidity Reading,"
                              "Trigger 1 Status,"
                              "Trigger 2 Status,"
                              "Passthrough RS-485 Status,"
                              "Magnetic Switch 1 Read Status,"
                              "Magnetic Switch 1 Time Difference,"
                              "Magnetic Switch 1 LED Status,"
                              "Magnetic Switch 2 Read Status,"
                              "Magnetic Switch 2 Time Difference,"
                              "Magnetic Switch 2 LED Status,"
                              "K64 LEDs Status,"
                              "Wi-Fi Network Status,"
                              "Wi-Fi LED and Communication Status,"                                                
                              "Itteration Time,"
                              "\n")
        

        
        ######################
        ## Setup Module Def ##
        ######################
            
        #Determine which modules to test for this program run
        moduleToTest = getModulesToTest() #Call the function to get module list
        masterModuleToTest = list(moduleToTest) #Master list to revert to for each board
        moduleName = ["Mod1  - 3V LDO",
                      "Mod2  - RS-485 driver, EE, and processor",
                      "Mod3  - RTC Clock & Battery",
                      "Mod4  - 3.3V SEPIC Converter",
                      "Mod5  - Serial Flash",
                      "Mod6  - SD Card",
                      "Mod7  - Priority Power Switch",
                      "Mod8  - System Current",
                      "Mod9  - 12V SEPIC Converter",
                      "Mod10 - 5V LDO",
                      "Mod11 - 12V Sensor Switch",
                      "Mod12 - Sensor Current",
                      "Mod13 - Priority Power Out Switch",
                      "Mod14 - Sensor Ports",
                      "Mod15 - Pressure/Temp/Humidity Chip",
                      "Mod16 - Triggers",
                      "Mod17 - RTU RS-485 Passthrough",
                      "Mod18 - Magnetic Switch",
                      "Mod19 - K64 LEDs",
                      "Mod20 - Wi-Fi Module"]
        moduleNumber=0 #Counter for which module is active

        ###################
        ## PCB Test Loop ##
        ###################

        sn = getSN(snlen) #Get the initial devices serial number
        retryAttempts=0 #Counter used when a PCB is re-tested after an failure occurs
        
        ##Continually loop through the test process to allow the user to test a batch of PCBs
        while (sn != "-1"): #Loop through all PCBs to be tested
            startTime=time.time()#Timestamp beginning time
            logging.debug("-------------ITTERATION START FOR SN: %s -------------",sn)

            out_records.write("%s" % sn) #Write serial number to file

            #Test the 3V LDO
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the 3V LDO...")
                result1=test3VLDO(GPIO,pinDict,x2,mbRetries,spi) #Call the 3V LDO test module
                print ("=====================")
                logging.info("Test results:\n"
                             "3V LDO Status: %s\n"
                             "3V LDO Voltage: %.3f"
                             ,result1[0],result1[1])
                out_records.write(",%s,%s" % (result1[0],result1[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result1[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("3V LDO Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the RS-485 driver, EE and processor
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Processor, EE, & RS-485 Modbus Communication...")
                result2=testProcEEAndRS485(GPIO,pinDict,x2,mbRetries) #Call the Processor and RS-485 test module
                print("=====================")
                logging.info("Test result:\n"
                             "Processor & Host RS-485 Status: %s\n"
                             "EE Chip Status: %s"
                             ,result2[0],result2[1])
                out_records.write(",%s,%s" % (result2[0],result2[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result2[0]=="Pass" and result2[1]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Processor, EE, & RS-485 Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the RTC Clock & Battery
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the RTC Clock...")
                result3=testRTC(GPIO,pinDict,x2,mbRetries) #Call the RTC Test module
                print("=====================")
                logging.info("Test result:\n"
                             "RTC Battery Read Status: %s\n"
                             "RTC Battery Voltage: %.3f\n"
                             "RTC Clock Retention Status: %s\n"
                             "RTC Clock Retention Difference: %.3f"
                             ,result3[0],result3[1],result3[2],result3[3])
                out_records.write(",%s,%s,%s,%s" % (result3[0],result3[1],result3[2],result3[3])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result3[0]=="Pass" and result3[2]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("RTC Clock & Battery Testing Skipped...")
                out_records.write(",skipped,skipped,skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the 3.3V SEPIC Converter
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the 3.3V SEPIC Converter...")
                result4=test33SEPIC(GPIO,pinDict,x2,mbRetries) #Call the 3.3V SEPIC test module
                print("=====================")
                logging.info("Test result:\n"
                             "3.3V SEPIC Status: %s\n"
                             "3.3V SEPIC Voltage: %.3f"
                             ,result4[0],result4[1])
                out_records.write(",%s,%s" % (result4[0],result4[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result4[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("3.3V SEPIC Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the Serial Flash
            moduleToTest[moduleNumber]=0 #Always skip for now
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Serial Flash...")
                result5=testSerialFlash(GPIO,pinDict,x2,mbRetries) #Call the serial flash test module
                print("=====================")
                logging.info("Test result:\n"
                             "Serial Flash Status: %s"
                             ,result5[0])
                out_records.write(",%s" % (result5[0])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result5[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Serial Flash Testing Skipped...")
                out_records.write(",skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test SD Card
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the SD Card...")
                result6=testSDCard(GPIO,pinDict,x2,mbRetries) #Call the SD Card test module
                print("=====================")
                logging.info("Test result:\n"
                             "SD Card Status: %s"
                             ,result6[0])
                out_records.write(",%s" % (result6[0])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result6[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("SD Card Testing Skipped...")
                out_records.write(",skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test Priority Power Switch
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Priority Power Switch...")
                result7=testPrioPwrPathSW(GPIO,pinDict,x2,mbRetries) #Call the PPSW test module
                print("=====================")
                logging.info("Test result:\n"
                             "Backup Power Switch Status: %s\n"
                             "Backup Power Voltage: %.3f\n"
                             "Backup Valid Line Value: %s\n"
                             "Secondary Power Switch Status: %s\n"
                             "Secondary Power Voltage: %.3f\n"
                             "Secondary Valid Line Value: %s\n"
                             "Primary Power Switch Status: %s\n"
                             "Primary Power Voltage: %.3f\n"
                             "Primary Valid Line Value: %s\n"
                             "PPP_1DISCON Status: %s\n"
                             "PPP_1DISCON Valid Line Value: %s"
                             ,result7[0],result7[1],bin(result7[2])
                             ,result7[3],result7[4],bin(result7[5])
                             ,result7[6],result7[7],bin(result7[8])
                             ,result7[9],bin(result7[10]))
                out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s" % (result7[0],result7[1],bin(result7[2]), #Write the results to the file
                                                                         result7[3],result7[4],bin(result7[5]),
                                                                         result7[6],result7[7],bin(result7[8]),
                                                                         result7[9],bin(result7[10])))
                print("------------------------------\n")
                #Clear flag if test passed
                if(result7[0]=="Pass" and result7[3]=="Pass" and result7[6]=="Pass" and result7[9]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Priority Power Switch Testing Skipped...")
                out_records.write(",skipped,skipped,skipped"
                                  ",skipped,skipped,skipped"
                                  ",skipped,skipped,skipped"
                                  ",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count
            
            #Test System Current
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the System Current...")
                result8=testSysCur(GPIO,pinDict,x2,mbRetries) #Call the system current test module
                print("=====================")
                logging.info("Test result:\n"
                             "System Current Status: %s\n"
                             "System Current Value: %.3f"
                             ,result8[0],result8[1])
                out_records.write(",%s,%s" % (result8[0],result8[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result8[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("System Current Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count
                

            #Test the 12V SEPIC Converter
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the 12V SEPIC Converter...")
                result9=test12SEPIC(GPIO,pinDict,x2,mbRetries) #Call the 12V SEPIC test module
                print("=====================")
                logging.info("Test result:\n"
                             "12V SEPIC Status: %s\n"
                             "12V SEPIC Voltage: %.3f"
                             ,result9[0],result9[1])
                out_records.write(",%s,%s" % (result9[0],result9[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result9[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("System Current Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the 5V LDO Converter
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the 5V LDO Converter...")
                result10=test5VLDO(GPIO,pinDict,x2,mbRetries,spi) #Call the 5V LDO test module
                print("=====================")
                logging.info("Test result:\n"
                             "5V LDO Status: %s\n"
                             "5V LDO Voltage: %.3f"
                             ,result10[0],result10[1])
                out_records.write(",%s,%s" % (result10[0],result10[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result10[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("5V LDO Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the 12V Sensor Switch
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the 12V Sensor Switch...")
                result11=test12VSenSW(GPIO,pinDict,x2,mbRetries,spi) #Call the 12V Sensor Switch test module
                print("=====================")
                logging.info("Test result:\n"
                             "12 Sensor Power Switch A Status: %s\n"
                             "12 Sensor Power Switch A Voltage: %.3f\n"
                             "12 Sensor Power Switch B Status: %s\n"
                             "12 Sensor Power Switch B Voltage: %.3f\n"
                             "12 Sensor Power Switch C Status: %s\n"
                             "12 Sensor Power Switch C Voltage: %.3f\n"
                             "12 Sensor Power Switch D Status: %s\n"
                             "12 Sensor Power Switch D Voltage: %.3f"
                             ,result11[0],result11[1]
                             ,result11[2],result11[3]
                             ,result11[4],result11[5]
                             ,result11[6],result11[7])
                out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s" % (result11[0],result11[1], #Write the results to the file
                                                                result11[2],result11[3],
                                                                result11[4],result11[5],
                                                                result11[6],result11[7]))
                print("------------------------------\n")
                #Clear flag if test passed
                if(result11[0]=="Pass" and result11[2]=="Pass" and result11[4]=="Pass" and result11[6]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("12V Sensor Switch Testing Skipped...")
                out_records.write(",skipped,skipped"
                                  ",skipped,skipped"
                                  ",skipped,skipped"
                                  ",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test Sensor Current
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Sensor Current...")
                result12=testSenCur(GPIO,pinDict,x2,mbRetries) #Call the system current test module
                print("=====================")
                logging.info("Test result:\n"
                             "12V Sensor Current Status: %s\n"
                             "12V Sensor Current Value: %.3f"
                             ,result12[0],result12[1])
                out_records.write(",%s,%s" % (result12[0],result12[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result12[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Sensor Current Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count
                

            #Test Priority Power Out Switch
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Priority Power Out Switch...")
                result13=testPrioPwrOutSW(GPIO,pinDict,x2,mbRetries,spi) #Call the priority power out switch test module
                print("=====================")
                logging.info("Test result:\n"
                             "Priority Power Output 1 Status: %s\n"
                             "Priority Power Output 1 Value: %.3f\n"
                             "Priority Power Output 2 Status: %s\n"
                             "Priority Power Output 2 Value: %.3f"
                             ,result13[0],result13[1]
                             ,result13[2],result13[3])
                out_records.write(",%s,%s,%s,%s" % (result13[0],result13[1],
                                                    result13[2],result13[3])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result13[0]=="Pass" and result13[2]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Priority Power Out Switch Testing Skipped...")
                out_records.write(",skipped,skipped"
                                  ",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the Sensor Ports
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Sensor Ports...")
                result14=testSensor(GPIO,pinDict,x2,mbRetries,modbusTimeout) #Call the Sensor port test module
                print("=====================")
                logging.info("Test result:\n"
                             "Port 0 RS-485 Sensor Status: %s\n"
                             "Port 0 RS-232 Sensor Status: %s\n"
                             "Port 0 SDI-12 Sensor Status: %s\n"
                             "Port 1 RS-485 Sensor Status: %s\n"
                             "Port 1 RS-232 Sensor Status: %s\n"
                             "Port 1 SDI-12 Sensor Status: %s\n"
                             "Port 2 RS-485 Sensor Status: %s\n"
                             "Port 2 RS-232 Sensor Status: %s\n"
                             "Port 2 SDI-12 Sensor Status: %s"
                             ,result14[0],result14[1],result14[2]
                             ,result14[3],result14[4],result14[5]
                             ,result14[6],result14[7],result14[8])
                out_records.write(",%s,%s,%s,%s,%s,%s,%s,%s,%s" % (result14[0],result14[1],result14[2],
                                                                   result14[3],result14[4],result14[5],
                                                                   result14[6],result14[7],result14[8],)) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result14[0]=="Pass" and result14[1]=="Pass" and result14[2]=="Pass" and
                   result14[3]=="Pass" and result14[4]=="Pass" and result14[5]=="Pass" and
                   result14[6]=="Pass" and result14[7]=="Pass" and result14[8]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Sensor Port Testing Skipped...")
                out_records.write(",skipped,skipped,skipped"
                                  ",skipped,skipped,skipped"
                                  ",skipped,skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test Pressure/Temp/Humidity
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the pressure, temperature, and humidity chip...")
                result15=testpressTempHum(GPIO,pinDict,x2,mbRetries) #Call the pressure temp. humidity test module
                print("=====================")
                logging.info("Test result:\n"
                             "Pressure/Temp/Humidity Chip Status: %s\n"
                             "Pressure Status: %s\n"
                             "Pressure Reading: %.3f\n"
                             "Temperature Status: %s\n"
                             "Temperature Reading: %.3f\n"
                             "Humidity Status: %s\n"
                             "Humidity Reading: %.3f"
                             ,result15[0]
                             ,result15[1],result15[2]
                             ,result15[3],result15[4]
                             ,result15[5],result15[6])
                out_records.write(",%s,%s,%s,%s,%s,%s,%s" % (result15[0],
                                                             result15[1],result15[2],
                                                             result15[3],result15[4],
                                                             result15[5],result15[6])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result15[0]=="Pass" and result15[1]=="Pass" and result15[3]=="Pass" and result15[5]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Pressure/Temp/Humidity Testing Skipped...")
                out_records.write(",skipped"
                                  ",skipped,skipped"
                                  ",skipped,skipped"
                                  ",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test Trigger
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Trigger Lines...")
                result16=testTriggers(GPIO,pinDict,x2,mbRetries) #Call the trigger lines test module
                print("=====================")
                logging.info("Test result:\n"
                             "Trigger 1 Status: %s\n"
                             "Trigger 2 Status: %s"
                             ,result16[0],result16[1])
                out_records.write(",%s,%s" % (result16[0],result16[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result16[0]=="Pass" and result16[1]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Trigger Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test RTU RS-485 Passthrough
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the RS-485 Passthrough...")
                result17=testRS485Passthrough(GPIO,pinDict,x2,mbRetries,tnode) #Call the RS-485 Passthrough test module
                print("=====================")
                logging.info("Test result:\n"
                             "RTU RS-485 Passthrough Status: %s"
                             ,result17[0])
                out_records.write(",%s" % (result17[0])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result17[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("RTU RS-485 Testing Skipped...")
                out_records.write(",skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the Magnetic Switch
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Magnetic Switch...")
                result18=testMagSW(GPIO,pinDict,x2,mbRetries,modbusTimeout) #Call the magnetic switch test module
                print("=====================")
                logging.info("Test result:\n"
                             "Magnetic Switch 1 Read Status: %s\n"
                             "Magnetic Switch 1 Time Difference: %.3f\n"
                             "Magnetic Switch 1 LED Status: %s\n"
                             "Magnetic Switch 2 Read Status: %s\n"
                             "Magnetic Switch 2 Time Difference: %.3f\n"
                             "Magnetic Switch 2 LED Status: %s"
                             ,result18[0],result18[1],result18[2]
                             ,result18[3],result18[4],result18[5])
                out_records.write(",%s,%s,%s,%s,%s,%s" % (result18[0],result18[1],result18[2],
                                                          result18[3],result18[4],result18[5])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result18[0]=="Pass" and result18[2]=="Pass" and result18[3]=="Pass" and result18[5]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("Magnetic Switch Testing Skipped...")
                out_records.write(",skipped,skipped,skipped"
                                  ",skipped,skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test K64 LEDs
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the K64 LEDs...")
                result19=testK64LEDs(GPIO,pinDict,x2,mbRetries) #Call the K64 LEDs test module
                print("=====================")
                logging.info("Test result:\n"
                             "K64 LEDs Status: %s"
                             ,result19[0])
                out_records.write(",%s" % (result19[0])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result19[0]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("K64 LED Testing Skipped...")
                out_records.write(",skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count

            #Test the Wi-Fi module (LEDs, Communication, Network)
            if(moduleToTest[moduleNumber]):
                print("\n------------------------------")
                logging.info("Testing the Wi-Fi Module...")
                result20=testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries) #Call the Processor and RS-485 test module
                print("=====================")
                logging.info("Test result:\n"
                             "Wi-Fi Network Status: %s\n"
                             "Wi-Fi LED and Communication Status: %s"
                             ,result20[0],result20[1])
                out_records.write(",%s,%s" % (result20[0],result20[1])) #Write the result to the file
                print("------------------------------\n")
                #Clear flag if test passed
                if(result20[0]=="Pass" and result20[1]=="Pass"):
                    moduleToTest[moduleNumber]=0
            else:
                print("\n------------------------------")
                logging.info("K64 LED Testing Skipped...")
                out_records.write(",skipped,skipped") #Write the result to the file
                print("------------------------------\n")
            moduleNumber += 1 #Increment the active module count



            #Mark end of board itteration
            endTime=time.time()#Timestamp ending time
            itterationTime=round(endTime-startTime,1)
            out_records.write(",%s" % (itterationTime))
            out_records.write("\n")#Line return to go to next record

            #Reset the module increment counter
            moduleNumber=0

            print("----------------------------------------------")
            logging.info("Board SN: %s has completed its itteration",sn)
            logging.info("The test took a total of %.3f seconds",itterationTime)
            print("----------------------------------------------\n\n")
            

            #Check for failed modules and allow retry
            leftToTest=sum(moduleToTest) #sum the number of modules left to test. These were changed to 0 above if the module passed.
            
            #If there were failures tell user and see if they want to rety those sections
            if(leftToTest>0):
                logging.info("The curent board has finished testing all sections.\n"
                      "There was/were %d failure(s).\n"
                      "The failed section(s) is/are:",leftToTest)
                for i in range(0,len(moduleToTest)): #Loop through and print out the sections that failed
                    if(moduleToTest[i]):
                        logging.info(moduleName[i])
                done=False
                while not (done):
                    retrySections = input("Would you like to retry the failed sections? (y/n): ")
                    if(retrySections == "y" or retrySections == "Y"):
                        retryTest=True
                        done=True
                    elif(retrySections == "n" or retrySections == "N"):
                        retryTest=False
                        done=True
                    else:
                        logging.info("\nYou must enter y or n. Try again.\n")
            else:
                retryTest=False
                logging.info("The board completed testing with no failures")

            #Decide whether to end itteration or re-loop
            if(retryTest):
                retryAttempts = retryAttempts+1
                sn = sn[0:snlen]+" --RETRY-- "+str(retryAttempts) #Set the serial number to "xxxx --Retry-- y"
            else:
                #Reset the modules for the next boards itteration to the original selection for this program run
                moduleToTest = masterModuleToTest

                #Turn off the power
                GPIO.output(pinDict["IO1"],GPIO.LOW)
                GPIO.output(pinDict["IO2"],GPIO.LOW)
                GPIO.output(pinDict["IO3"],GPIO.LOW)
                GPIO.output(pinDict["IO4"],GPIO.LOW)

                #Set retry attempts back to 0 for next board
                retryAttempts=0
                    
                #End current board itteration
                input("\nThe current board has finished testing and is safe to remove.\n"
                      "Please remember to remove the SD Card\n\n"
                      "Press Enter to continue\n")

                #Prepare for next board
                out_records.flush()
                sn = getSN(snlen) #Get new board SN

    #Define operation when an exception occurs
    except KeyboardInterrupt:
        out_records.write(",KEYBOARD INTERRUPT ERROR\n")#Line return to go to next record
        out_records.flush()        
        print("\n==============================\n")
        logging.error("The program was cancelled by a keyboard interrupt!\n")
        print("==============================\n")
        input("Press Enter to exit\n")
    except Exception as error:
        out_records.write(",PROGRAM ERROR,")
        out_records.write(str(error))
        out_records.write("\n")#Line return to go to next record
        out_records.flush()
        print("\n==============================\n")
        logging.error("The program encountered the following error!\n")
        logging.error("Error Type: %s", type(error))
        logging.error(error.args)
        logging.error(error)
        print("==============================\n")
        input("Press Enter to exit\n")
    finally:
        logging.info("Cleaning up and exiting...")
        out_records.close #Close the file
        GPIO.output(pinDict["IO1"],GPIO.LOW) #Turn power off to Primary Power
        GPIO.output(pinDict["IO2"],GPIO.LOW) #Turn power off to Secondary Power
        GPIO.output(pinDict["IO3"],GPIO.LOW) #Turn power off to Backup Power
        GPIO.output(pinDict["IO4"],GPIO.LOW) #Turn power off to T-Node
        GPIO.cleanup() #Clean up GPIOs
        logging.shutdown() #Stops the logging process



###############
## Functions ##
###############

# This function is able to take up to 4 16-bit hex values as a list and
# combine them into a single integer
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
    logging.debug("Reading %s Status...",clearText)
    readResult = mbReadRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries)
    if(readResult): #if the read was successful
        if(readResult[0]==1): #check if status was good
            logging.debug("The %s status is good",clearText)
            return [readResult[0],"Pass"]
        elif(readResult[0]==0): #bad
            logging.debug("The %s status is bad",clearText)
            return [readResult[0],"Fail-The "+clearText+" status was returned as bad"]
        else: #or unknown
            logging.debug("The %s status is unknown",clearText)
            return [readResult[0],"Fail-The "+clearText+" status was returned as an unknown value"]
    else:
        logging.debug("The read was not successful")
        return [-999999,"Fail-The Modbus read failed. No status received"]

#Generic function to enable or disable any of the X2's switches
def enableDisable(x2,mbRetries,mbDictName,clearText,onOff):
    #Modbus Device, # MB retries, MB Dictionary Name, Readable text, True=On/False=Off
    
    #Toggle the switch
    if(onOff): #if the call was to enable the switch
        #Turn the switch on
        logging.debug("Enabling the %s ...",clearText)
        writeResult1 = mbWriteRetries(x2,Reg.mbReg[mbDictName][0],[1],retries=mbRetries) #1=on
        if(writeResult1):
            logging.debug("The %s was successfully enabled",clearText)
            return True
        else:
            logging.debug("Enabling the %s was not successful",clearText)
            return False
    else:#if the call was to disable the switch
        #Turn the switch off
        logging.debug("Disabling the %s ...",clearText)
        writeResult2 = mbWriteRetries(x2,Reg.mbReg[mbDictName][0],[0],retries=mbRetries) #0=off
        if(writeResult2):
            logging.debug("The %s was successfully disabled", clearText)
            return True
        else:
            logging.debug("Disabling the %s was not successful", clearText)
            return False

#Determine which modules should be tested
def getModulesToTest():

    #Copy the master file to the desktop for user manipulation
    shutil.copy2("/home/pi/Documents/GitHub/X2Tester/ModuleToTest.txt","/home/pi/Desktop/ModuleToTest.txt")

    input("If only certain modules are to be tested for this run, please update the\n"
          "ModuleToTest.txt file that is currently on the Desktop.\n\n"
          "After making any modifications, please save the file and hit ENTER.\n"
          "Otherwise just hit ENTER\n\n")               

    #Open the file for reading
    in_moduleToTestFile=open("/home/pi/Desktop/ModuleToTest.txt", 'r')

    #Read in the file's values
    moduleToTest=[] #start with an empty list
    for i in range(0,20):
        moduleToTest.append(int(in_moduleToTestFile.readline()[0:1]))#Read in just the first character of each row and add to the list

    #close the file
    in_moduleToTestFile.close()
    
    #delete the file from the desktop
    os.remove("/home/pi/Desktop/ModuleToTest.txt")

    return moduleToTest

#Used to get the PCB's serial number and ensure it is valid
def getSN(snlen):
    #Get the SN from the user
    sn = input("Please do the following (Enter -1 if done):\n"
               "1) Insert the SD Card\n"
               "2) Connect the PCB\n"
               "3) Enter the PCB's serial number followed by ENTER\n"
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

#Magnet Switch Test
#Asks user to trigger the switch then compares the trigger time to current time
def magSWCheck(x2,mbRetries,mbDictName,magSWNum):
    
    #Prompt user to trigger switch and then get user input for LED
    done=False
    while not(done):
        magraw= input("\nPlease use a magnet to trigger magnetic switch "+magSWNum+".\n"
                      "Did the corresponding LED light up when triggered (y/n)?: ")
        if(magraw=="y" or magraw =="Y"):
            logging.info("The LED has been marked as working\n")
            magLEDStat="Pass"
            done=True
        elif(magraw=="n" or magraw=="N"):
            logging.info("The LED has been marked as NOT working\n")
            magLEDStat="Fail-LED did not illuminate"
            done=True
        else:
            logging.info("\nYou must enter y or n for you response. Please try again.\n")
            #Turn off the Wi-Fi so it doesn't interfere on the RS-485 bus
            enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)

    #Turn off the Wi-Fi so it doesn't interfere on the RS-485 bus
    enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)

    #Check the time since last magnet and ensure it was recent
    #Read the current device time
    TimeReadResult = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries) #Read from the X2
    if(TimeReadResult):
        readTime=[TimeReadResult[0],TimeReadResult[1]] #The first two 16 bits are the time, the next two are the tz offset
        convResult1 = combineFrom16Bits(readTime) #Convert to a single 32-bit time
        formatedDateTime1 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult1)) # Convert from Epoch to readable
        logging.debug("The device's original time is %s\n",formatedDateTime1)

        #Read the time the magnet was last triggered
        logging.debug("Reading the time since last magnet trigger...")
        magnetTimeReadResult = mbReadRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries) #Read from the X2
        if(magnetTimeReadResult):
            convResult2=combineFrom16Bits(magnetTimeReadResult) #Convert to a single 32-bit time
            formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult2)) # Convert from Epoch to readable
            logging.debug("The last magnet read time is %s\n",formatedDateTime2)

            #Compare the two times
            logging.debug("Comparing the two times...")
            timeDiff = abs(convResult1 - convResult2)
            if(timeDiff < 60):
                logging.debug("Success - The time difference is %d seconds. The max acceptable difference is 60 seconds",timeDiff)
                magReadStat="Pass"
            else:
                logging.debug("Failure - The time difference is %d seconds. The max acceptable difference is 60 seconds",timeDiff)
                magReadStat="Fail-Time between last read and current time is too great"
        else:
            logging.debug("Reading time since last magnet trigger was not successful")
            magReadStat="Fail-Reading time since last magnet trigger was not successful"
    else:
        logging.debug("Reading current time was not successful")
        magReadStat="Fail-Reading current time was not successful"

    return [magReadStat,timeDiff,magLEDStat]

#This function is used to gracefully handle failed float value reads and allow retries 
def mbReadFloatRetries(device,reg,numReg=2,retries=5): #(Minimalmodbus device),(Register address),(Number of registers to read),(Retry attempts)
    for i in range (0,retries):
        try:
            device.serial.flushInput() #clear serial buffer before reading
            result=device.read_float(reg,functioncode=4,numberOfRegisters=numReg)
            result=round(result,3)
            break #if it gets past the read without causing an exception exit the loop as the read was successful
        except:
            logging.debug("Reading %d Failed",i)
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
            logging.debug("Reading %d Failed",i)
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
            logging.debug("Writing %d Failed",i)
            pass #Continue running the code without exiting the program if the read was not successful
    else: #If it exits normally that means it failed every time
        return False
    return value
#Returns False if it fails and the values that were written if successful

#Used to check the current status of the PCB's power and disable power if it is on
def powerOff(GPIO,pinDict,pinValue,delay=5):
    logging.debug("Powering %s off...",pinValue)
    if(GPIO.input(pinDict[pinValue])== 1):
        GPIO.output(pinDict[pinValue],GPIO.LOW)
        time.sleep(delay)
    return True

#Used to check the current status of the PCB's power and enable power if it is off
def powerOn(x2,mbRetries,GPIO,pinDict,pinValue,delay=3):
    logging.debug("Powering %s on...",pinValue)
    if(GPIO.input(pinDict[pinValue])== 0):
        GPIO.output(pinDict[pinValue],GPIO.HIGH)
        #The sleep time of 1 works in IDLE, but not in the cmd line
        #Not sure reason, but possible execution speed is faster in cmd line
        time.sleep(delay)

        #If not turning on T-Node disable the Wi-Fi
        if(pinValue!="IO4"):
            #Turn off the Wi-Fi so it doesn't interfere on the RS-485 bus
            enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)
            
    return True

#Tests the voltage and valid line status for a power input channel
def prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,mbDictName,validCheck,validValue):

    #Read the Channel Voltage
    logging.debug("Reading Channel Voltage...")
    readResult1 = mbReadFloatRetries(x2,Reg.mbReg[mbDictName][0],Reg.mbReg[mbDictName][1],retries=mbRetries)
    if(readResult1):
        chVoltage=readResult1[0]
        logging.debug("The channel voltage level is %.3f\n",chVoltage)
        
        #Check if voltage is in range
        rangeCheck=valueRangeCheck(12.0,2,chVoltage)#Expected, tolerance, test input
        chVoltageStat=rangeCheck[0]#True if in range and False if out of range
    else:
        logging.debug("The channel voltage read was not successful\n")
        chVoltage="Fail-Reading the channel voltage was not successful"
        chVoltageStat=False

    if(validCheck):#Only try if the 3.3V SEPIC was turned on successfully
        #Read the Valid Lines
        logging.debug("\nReading the valid lines")
        readResult2 = mbReadRetries(x2,Reg.mbReg["Valid"][0],Reg.mbReg["Valid"][1],retries=mbRetries)
        if(readResult2):
            logging.debug("The valid lines read %s",bin(readResult2[0]))
            if(readResult2[0]== validValue): #If read was successful check the correct lines are enabled
                logging.debug("The correct valid lines were enabled\n")
                chValid=readResult2[0]
                chValidStat=True
            else:
                logging.debug("The incorrect valid lines were enabled")
                chValid=readResult2[0]
                chValidStat=False
        else:
            logging.debug("Reading the valid lines was not successful")
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

#Test an individual sensor port's voltage
def sensor12VSW(GPIO,pinDict,x2,mbRetries,spi,mbDictName,clearText,spiCh):
    
    #Enable 12V SW
    if(enableDisable(x2,mbRetries,mbDictName,clearText,1)):
        #If successfully enabled check the output voltage
        logging.debug("Reading 12V %s Voltage...",clearText)
        scaling=scaleValue(27.4,10) #Determine voltage divider scaling value
        analog = readAnalog(spi,spiCh,scaling) #Read SPI0 ch. 1
        logging.debug("The read voltage is %.3f\n",analog)

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(12,0.5,analog)#Expected, tolerance, test input

        return [rangeCheck[1],analog]
    else:
        return ["Fail-Unable to enable"+clearText,-999999]

#Tests the sensor port's communication
def sensorTest(x2,mbRetries,RS232Channel):

    #Send RS-485 Command
    logging.debug("\nTesting RS-485 Communicaiton")
    [portValue485,portStatus485]=checkStatus(x2,mbRetries,"RS485ComTest","RS-485 Communication Test")

    #Send RS-232 Command
    logging.debug("\nTesting RS-232 Communicaiton")
    [portValue232,portStatus232]=checkStatus(x2,mbRetries,RS232Channel,"RS-232 Communication Test")

    #Send SDI-12 Command
    logging.debug("\nTesting SDI-12 Communicaiton")
    [portValueSDI12,portStatusSDI12]=checkStatus(x2,mbRetries,"SDI12ComTest","SDI-12 Communication Test")

    return [portStatus485,portStatus232,portStatusSDI12]

# This function take a 16,32,48, or 64 bit value and split it into a list of 16-bit values
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
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    time.sleep(.1) #needed to let 12V SEPIC stabalize

    #Read the 12V SEPIC voltage
    logging.debug("Reading 12V SEPIC Voltage...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["12VSen_V"][0],Reg.mbReg["12VSen_V"][1],retries=mbRetries)
    if(readResult):
        logging.debug("The 12V SEPIC voltage level is %.3f\n",readResult[0])

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(12,0.5,readResult[0])#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off SEPIC
        return[rangeCheck[1],readResult[0]]
    else:
        logging.debug("The 12V SEPIC voltage read was not successful\n")
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off SEPIC
        return ["Fail-Reading the 12V SEPIC voltage was not successful",-999999]

#Test 12V Sensor Switch
def test12VSenSW(GPIO,pinDict,x2,mbRetries,spi):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999,
                "Fail-Enabling the 12V SEPIC was not successful",-999999
                ]

    time.sleep(.1) #needed to let 12V SEPIC stabalize

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
            sensorDStatus,sensorDVLevel]
    
#Test the 3.3V SEPIC
def test33SEPIC(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1) == False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the 3.3V SEPIC voltage
    logging.debug("\nReading 3.3V SEPIC Voltage...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["VCC33_V"][0],Reg.mbReg["VCC33_V"][1],retries=mbRetries)
    if(readResult):
        logging.debug("The 3.3V SEPIC voltage level is %.3f",readResult[0])

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(3.3,0.1,readResult[0])#Expected, tolerance, test input

        return[rangeCheck[1],readResult[0]]
    else:
        logging.debug("The 3.3V SEPIC voltage read was not successful\n")
        return ["Fail-Reading the 3.3V SEPIC voltage was not successful",-999999]

#Test the 3V LDO is functioning correctly
def test3VLDO(GPIO,pinDict,x2,mbRetries,spi):   
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    logging.debug("\nReading 3V LDO Voltage...")
    analog0 = readAnalog(spi,0) #Read SPI0 ch. 0
    logging.debug("The read voltage is %.3f",analog0)

    #Check if voltage is in range and return the result
    rangeCheck=valueRangeCheck(3.0,0.3,analog0)#Expected, tolerance, test input

    return[rangeCheck[1],analog0]

#Test the 5V LDO is functioning correctly
def test5VLDO(GPIO,pinDict,x2,mbRetries,spi):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Enable 5V LDO
    if(enableDisable(x2,mbRetries,"5VLDO_OF","5V LDO",1)):
        #If successfully enabled check the output voltage
        logging.debug("\nReading 5V LDO Voltage...")
        scaling=scaleValue(6.04,10)
        analog1 = readAnalog(spi,1,scaling) #Read SPI0 ch. 1
        logging.debug("The read voltage is %.3f",analog1)

        #Check if voltage is in range and return the result
        rangeCheck=valueRangeCheck(5.0,0.1,analog1)#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"5VLDO_OF","5V LDO",0)#Turn off 5V LDO
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC

        return [rangeCheck[1],analog1]
    else:
        enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC
        return ["Fail-Enabling the 5V LDO was not successful",-999999]

#Test the K64 LEDs turn on
def testK64LEDs(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1) == False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful"]

    #Enable the Wi-Fi LEDs
    logging.debug("\nTesting the K64 LEDs...")
    writeResult1 = mbWriteRetries(x2,Reg.mbReg["K64LED"][0],[1],retries=mbRetries)#0 = LEDs on; 1 = LEDs off
    if(writeResult1):
        logging.debug("The LEDs were enabled")

        #Check if LEDs were enabled
        done=False
        while not(done):
            LEDUserInput = input("Did all 4 K64 LEDs come on? (y/n): ")
            if(LEDUserInput == "y" or LEDUserInput == "Y"):
                logging.info("\nSuccess - You indicated that the LEDs were enabled\n")
                LEDStatus = "Pass"
                done=True
            elif (LEDUserInput == "n" or LEDUserInput == "n"):
                logging.info("\nFailure -  You indicated that the LEDs were not all enabled\n")
                LEDStatus = "Fail-All LEDs were not turned on"
                done=True
            else:
                logging.info("\nYou must enter y or n. Try again.\n")
                done=False
    else:
        LEDStatus="Fail-Turning the LEDs on was not successful"

    #Turn the LEDs back off
    logging.debug("Turning the LEDs back off...")
    writeResult2 = mbWriteRetries(x2,Reg.mbReg["K64LED"][0],[0],retries=mbRetries)#0 = LEDs on; 1 = LEDs off
    if(writeResult2):
        logging.debug("LEDs were successfully disabled")
    else:
        logging.debug("Disabling the LEDs failed")

    return [LEDStatus]

#Test the magnetic switches are working correctly
def testMagSW(GPIO,pinDict,x2,mbRetries,modbusTimeout):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Set the Modbus timeout to 1 seconds to prevent failure since Wi-Fi is turned
    #on when the magnet wakeup is triggered and we don't have control over timeing
    #since it depends on the user's input speed
    x2.serial.timeout = 1

    #Get user input for first magnet
    [mag1ReadStat,timeDiff1,mag1LEDStat]= magSWCheck(x2,mbRetries,"MagIntTest0","one")

    #Get user input for second magnet
    [mag2ReadStat,timeDiff2,mag2LEDStat]= magSWCheck(x2,mbRetries,"MagIntTest1","two")

    #Set the Modbus timeout back to the program default
    x2.serial.timeout = modbusTimeout

    return [mag1ReadStat,timeDiff1,mag1LEDStat,mag2ReadStat,timeDiff2,mag2LEDStat]

#Test pressure temperature and humidity chip
def testpressTempHum(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1) == False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999,
                "Fail-Enabling the 3.3V SEPIC was not successful",-999999,
                "Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the internal sensor chip's values
    logging.debug("\nReading pressure, temperature, and humidity chip...")
    readResult = mbReadRetries(x2,Reg.mbReg["ReadInternalSens"][0],Reg.mbReg["ReadInternalSens"][1],retries=mbRetries)
    if(readResult):
        sensorStatus="Pass"
        
        #Convert first two registers to the pressure reading
        pressureRaw=[readResult[0],readResult[1]]#First two registers are for pressure
        pressureComb=combineFrom16Bits(pressureRaw)#Combine into a single value
        pressureValue=round(struct.unpack('!f',bytes.fromhex(hex(pressureComb)[2:]))[0],3)#Convert to IEEE floating point
        logging.debug("\nThe pressure reading is: %.3f mBar\n",pressureValue)

        #Check pressure is in range
        [checkState1,pressureStatus]=valueRangeCheck(1000,500,pressureValue)#Expected, tolerance, test input

        #Convert next two registers to the temperature reading
        temperatureRaw=[readResult[2],readResult[3]]#Next two registers are for temperature
        temperatureComb=combineFrom16Bits(temperatureRaw)#Combine into a single value
        temperatureValue=round(struct.unpack('!f',bytes.fromhex(hex(temperatureComb)[2:]))[0],3)#Convert to IEEE floating point
        logging.debug("\nThe temperature reading is: %.3f degrees C\n",temperatureValue)

        #Check temperature is in range
        [checkState2,temperatureStatus]=valueRangeCheck(20,15,temperatureValue)#Expected, tolerance, test input

        #Convert last two registers to the humidity reading
        humidityRaw=[readResult[4],readResult[5]]#Last two registers are for humidity
        humidityComb=combineFrom16Bits(humidityRaw)#Combine into a single value
        humidityValue=round(struct.unpack('!f',bytes.fromhex(hex(humidityComb)[2:]))[0],3)#Convert to IEEE floating point
        logging.debug("\nThe humidity reading is: %.3f percent\n",humidityValue)

        #Check humidity is in range
        [checkState3,humidityStatus]=valueRangeCheck(50,45,humidityValue)#Expected, tolerance, test input

    else:
        logging.debug("Failed to read from the internal pressure, temperature, humidity chip")
        sensorStatus="Fail-Reading internal sensor was not successful"
        pressureValue=-999999
        temperatureValue=-999999
        humidityValue=-999999

   
    return [sensorStatus,pressureStatus,pressureValue,temperatureStatus,temperatureValue,humidityStatus,humidityValue]

#Test the priority power path out switch is working correctly
def testPrioPwrOutSW(GPIO,pinDict,x2,mbRetries,spi):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")


    #Enable Priority Power Out Switch
    if(enableDisable(x2,mbRetries,"PriPwr_OF","Priority Power Out Switch",1)):
        #If successfully enabled check the output voltage
        logging.debug("\nReading Output Voltages...")
        scaling=scaleValue(82.5,10)#Voltage divider X factor
        analog6 = readAnalog(spi,6,scaling) #Read SPI0 ch. 6
        analog7 = readAnalog(spi,7,scaling) #Read SPI0 ch. 7
        logging.debug("The J7 board to board read voltage is %.3f",analog6)
        logging.debug("The J3 JST read voltage is %.3f\n",analog7)

        #Check if voltage is in range and return the result
        rangeCheck1=valueRangeCheck(12,1,analog6)#Expected, tolerance, test input
        rangeCheck2=valueRangeCheck(12,1,analog7)#Expected, tolerance, test input

        enableDisable(x2,mbRetries,"PriPwr_OF","Priority Power Out Switch",0)#Turn off prio. pwr. out sw.

        return [rangeCheck1[1],analog6,
                rangeCheck2[1],analog7]       
    else:
        return ["Fail-Enabling priority power out switch was not successful",-999999,
                "Fail-Enabling priority power out switch was not successful",-999999]

#Test the priority power path switch is working correctly
def testPrioPwrPathSW(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO3",delay=3)#Enable the backup power input
    powerOff(GPIO,pinDict,"IO1",delay=0)#Ensure Primary input is off
    powerOff(GPIO,pinDict,"IO2",delay=0)#Ensure Secondary input is off

    #Enable 3.3V SEPIC and set a flag on whether to test the valid lines
    validCheck = enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)

    ##Test backup input
    logging.debug("\nTesting the Backup Input...\n")
    [bakStat,bakVoltage,bakValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"BakPwr_V",validCheck,0b100)

    ##Test secondary input
    powerOn(x2,mbRetries,GPIO,pinDict,"IO2",delay=1)#Enable secondary input
    
    logging.debug("\nTesting the Secondary Input...\n")
    [secStat,secVoltage,secValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"SecPwr_V",validCheck,0b110)

    ##Test primary input
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1",delay=1)#Enable primary input
    
    logging.debug("\nTesting the Primary Input...\n")
    [priStat,priVoltage,priValid]=prioPwrChannelTest(GPIO,pinDict,x2,mbRetries,"PriPwr_V",validCheck,0b111)

    ##Test PPP_1DISCON
    logging.debug("\nTriggering disconnect of Primary Power...\n")
    #Enabled the PPP_1DISCON pin to pull UV of Primary to GND
    writeResult1 = mbWriteRetries(x2,Reg.mbReg["PPP_Dis"][0],[1],retries=mbRetries)#0 (default) = pri on; 1 = pri off
    if(writeResult1):
        logging.debug("The primary power has been disabled")
        #Read the valid lines
        readResult = mbReadRetries(x2,Reg.mbReg["Valid"][0],Reg.mbReg["Valid"][1],retries=mbRetries)
        if(readResult):
            PPP_DisValid=readResult[0]
            logging.debug("The valid lines read %s",bin(PPP_DisValid))
            if(readResult[0]== 0b110): #If read was successful check the correct lines are enabled
                logging.debug("The correct valid lines were enabled")
                PPP_DisStatus="Pass"
            else:
                logging.debug("The incorrect valid lines were enabled")
                PPP_DisStatus="Fail-The incorrect valid lines were set"
        else:
            logging.debug("Reading the valid lines was not successful")
            PPP_DisStatus="Fail-Reading the valid lines was not successful"
            PPP_DisValid=-999999

        #Unset the Priority Power disconnect to prevent an unnecessary power cycle
        logging.debug("Re-enabling the primary power input...")
        writeResult2 = mbWriteRetries(x2,Reg.mbReg["PPP_Dis"][0],[0],retries=mbRetries)#0=pri on; 1=pri off
        if(writeResult2):
            time.sleep(1)#Pause to make sure it is back online before continuing
            logging.debug("The primary power has been enabled")
        else:
            logging.debug("Re-enabling the primary power failed")
    else:
        logging.debug("The write was not successful")
        PPP_DisStatus="Fail-Disabling primary power failed"
        PPP_DisValid=-999999
    
    #Disable secondary and backup inputs
    powerOff(GPIO,pinDict,"IO2",delay=0)
    powerOff(GPIO,pinDict,"IO3",delay=0)

    return [bakStat,bakVoltage,bakValid,secStat,secVoltage,secValid,priStat,priVoltage,priValid,PPP_DisStatus,PPP_DisValid]


#Test that the RS-485 and processor are functioning correctly
def testProcEEAndRS485(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Read the current address
    logging.debug("\nReading address...")
    readResult1 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
    if(readResult1):
        logging.debug("The device's original address is %d\n",readResult1[0])
    else:
        logging.debug("The read was not successful\n")
        return ["Fail-Initial read was not successful","Fail-EE not tested"]

    #Write a new address
    logging.debug("Writing address...")
    if(readResult1[0]==1): #If the current address is already 1, change to 2, then back to 1
        writeResult1 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[2],retries=mbRetries)
        if(writeResult1):
            logging.debug("The device's new address is %d",writeResult1[0])
        else:
            logging.debug("The write was not successful")
            return ["Fail-Writing address was not successful","Fail-EE not tested"]

        #Cycle the power to confirm address is written to and can be read from EE
        logging.debug("\nTesting EE Chip")
        logging.debug("Power cycling to confirm EE works...")
        powerOff(GPIO,pinDict,"IO1")
        logging.debug("Power off")
        powerOn(x2,mbRetries,GPIO,pinDict,"IO1")
        logging.debug("Power on\n")

        #Read address and confirm it is still 2 after the power cycle
        readResult2 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
        if(readResult2):
            logging.debug("The devices address is now %d",readResult2[0])
            if(readResult2[0]==2):
                logging.debug("The address was retained on power cycle")
                EEResult="Pass"
            else:
                logging.debug("The address was not retained on power cycle. EE Test Failed.")
                EEResult="Fail-Address not retained in EE"
        else:
            logging.debug("Reading address after EE power cycle was not successful")
            EEResult = "Fail-EE not tested"
            return ["Fail-Reading address after EE power cycle was not successful",EEResult]
        
        #Change the address back to 1
        writeResult2 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)#Change address back to 1
        if(writeResult2):
            logging.debug("The device's address was set back to %d",writeResult2[0])
        else:
            logging.debug("The write was not successful")
            return ["Fail-Changing address back to 1 was not successful",EEResult]
        time.sleep(0.01) #Without this the address doesn't read back right

        #Confirm the address is 1
        readResult3 = mbReadRetries(x2,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
        if(readResult3):
            logging.debug("The device's final address is %d",readResult3[0])
            return ["Pass",EEResult]
        else:
            logging.debug("Resetting the address to %d was not successful" % writeResult2[0])
            return ["Fail-Final read was not successful",EEResult]

    else: #If the address is anything besides 1, change to 1
        writeResult3 = mbWriteRetries(x2,Reg.mbReg["Add"][0],[1],retries=mbRetries)
        if(writeResult3):
            logging.debug("The device's new address is %d",writeResult3[0])
            return ["Pass","Pass"] #Assume EE is OK, since address started as a non default value (1)
        else:
            logging.debug("The write was not successful")
            return ["Fail-Writing address was not successful","Pass"] #Assume EE is OK, since address started as a non default value (1)

#Test RS-485 Passthrough
def testRS485Passthrough(GPIO,pinDict,x2,mbRetries,tnode):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO4")

    logging.debug("Reading address from the RS-485 passthrough T-Node...")
    readResult = mbReadRetries(tnode,Reg.mbReg["Add"][0],Reg.mbReg["Add"][1],retries=mbRetries)
    if(readResult):
        logging.debug("The RS-485 passthrough T-Node was read successfully")
        return ["Pass"]
    else:
        logging.debug("The RS-485 passthrough T-Node was not read successfully")
        return ["Fail-T-Node did not respond"]

#Test RTC Battery Functionality
def testRTC(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")
  
    #Read the RTC Voltage
    logging.debug("Reading the RTC Voltage...")
    RTCRawResult = mbReadFloatRetries(x2,Reg.mbReg["RTCBAT_V"][0],Reg.mbReg["RTCBAT_V"][1],retries=mbRetries)
    if(RTCRawResult):
        RTCVoltageValueResult = RTCRawResult[0]
        logging.debug("The RTC Battery voltage is %.3f\n",RTCVoltageValueResult)
        [rangeCheck,RTCVoltageRangeResult]=valueRangeCheck(3.0,0.2,RTCVoltageValueResult)
    else:
        logging.debug("The RTC Battery voltage read was not successful\n")
        RTCVoltageValueResult=-999999
        RTCVoltageRangeResult="Fail-Voltage read not successful"

    #Read the current time
    logging.debug("Reading Time from X2...")
    initialTimeReadResult = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries) #Read from the X2
    if(initialTimeReadResult):
        readTime1=[initialTimeReadResult[0],initialTimeReadResult[1]] #The first two 16 bits are the time, the next two are the tz offset
        convResult1 = combineFrom16Bits(readTime1) #Convert to a single 32-bit time
        formatedDateTime1 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult1)) # Convert from Epoch to readable
        logging.debug("The device's original time is %s\n",formatedDateTime1)

        #Write the current system time
        logging.debug("Writing Current Time...")
        currentPCTime=int(time.time()) #Read the current time from the system
        formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(currentPCTime)) # Convert from Epoch to readable
        logging.debug("Current computer time is: %s",formatedDateTime2)
        timeIn16bit = splitInto16Bits(currentPCTime) # Convert into separate 16-bit values
        tzOffset1=0 # Set the time zone offset to 0 for UTC time
        tzOffset2=0
        writeResult = mbWriteRetries(x2,Reg.mbReg["SetTime"][0],[timeIn16bit[0],timeIn16bit[1],tzOffset1,tzOffset2]) #Write to X2
        if(writeResult):
            logging.debug("Writing current computer time to X2 was successful\n")

            #Check if the board keeps time on a power cycle
            logging.debug("Cycling Power to board...")
            powerOff(GPIO,pinDict,"IO1")
            logging.debug("Turning board back on and checking time is accurate")
            powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

            #Read the boards current time
            logging.debug("\nReading Time from X2...")
            finalTimeReadResult = mbReadRetries(x2,Reg.mbReg["ReadTime"][0],Reg.mbReg["ReadTime"][1],retries=mbRetries) #Read from the X2
            if(finalTimeReadResult):
                readTime2=[finalTimeReadResult[0],finalTimeReadResult[1]] #The first two 16 bits are the time, the next two are the tz offset
                convResult2 = combineFrom16Bits(readTime2) #Convert to a single 32-bit time
                formatedDateTime2 = time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(convResult2)) # Convert from Epoch to readable
                logging.debug("The device's final time is %s\n",formatedDateTime2)

                timeDiff = convResult2 - int(time.time()) #Determine if time is saved

                if (timeDiff >= -5 and timeDiff <= 5):
                    logging.debug("Success! The RTC Clock was %d seconds off",timeDiff)
                    timeDiffResult="Pass"
                else: #If time difference is wrong
                    logging.debug("Failure! The RTC Clock was %d seconds off",timeDiff)
                    timeDiffResult="Fail"
            else: #If final time read fails
                logging.debug("The final time read was not successful\n")
                timeDiff=-999999
                timeDiffResult="Fail-Final time read not successful"
        else: #if time write fails
            logging.debug("The time write was not successful\n")
            timeDiff=-999999
            timeDiffResult="Fail-Time write not successful"            
    else: #If the initial time read fails
        logging.debug("The initial time read was not successful\n")
        timeDiff=-999999
        timeDiffResult="Fail-Initial time read not successful"        

    return [RTCVoltageRangeResult,RTCVoltageValueResult,timeDiffResult,timeDiff]

#Test SD Card is working
def testSDCard(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)==False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read the SD Card Status
    [statusValue,statusResult]=checkStatus(x2,mbRetries,"SDTest","SD card")

    return [statusResult]

#Test that the system current is reading correctly
def testSenCur(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 12V SEPIC
    if(enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",1)== False):
        return ["Fail-Enabling the 12V SEPIC was not successful",-999999]

    #Enable switch port A
    if(enableDisable(x2,mbRetries,"12V_A_OF","12V Port A",1)== False):
        return ["Fail-Enabling 12V Port A was not successful",-999999]

    #Read sensor current
    logging.debug("\nReading the sensor current...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["SenCur"][0],Reg.mbReg["SenCur"][1],retries=mbRetries)
    if(readResult):
        curr=readResult[0]
        currentLevel=valueRangeCheck(5,3,curr)
    else:
        logging.debug("The read was not successful")
        return ["Fail-The Modbus read failed",-999999]

    enableDisable(x2,mbRetries,"12V_A_OF","12V Sensor Port A",0)#Turn off port A after
    enableDisable(x2,mbRetries,"12SEPIC_OF","12V SEPIC",0)#Turn off 12V SEPIC after

    return [currentLevel[1],curr]

#Test Sensor Ports
def testSensor(GPIO,pinDict,x2,mbRetries,modbusTimeout):
    logging.debug("Module Start")
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

    #Set the Modbus timeout to 3 seconds during sensor testing so they have time to respond
    x2.serial.timeout = 3

    ##Test Port 0
    #Enable switch port A
    if(enableDisable(x2,mbRetries,"12V_A_OF","12V Port 0",1)):
        logging.debug("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port0Status = sensorTest(x2,mbRetries,"RS232AComTest")#Call function to test communication on Port 0
        enableDisable(x2,mbRetries,"12V_A_OF","12V Port 0",0)
    else:
        port0Status = ["Fail-Enabling 12V Port A was not successful",
                       "Fail-Enabling 12V Port A was not successful",
                       "Fail-Enabling 12V Port A was not successful"]

    ##Test Port 1
    #Enable switch port B
    if(enableDisable(x2,mbRetries,"12V_B_OF","12V Port 1",1)):
        logging.debug("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port1Status = sensorTest(x2,mbRetries,"RS232BComTest")#Call function to test communication on Port 1
        enableDisable(x2,mbRetries,"12V_B_OF","12V Port 1",0)
    else:
        port1Status = ["Fail-Enabling 12V Port 1 was not successful",
                       "Fail-Enabling 12V Port 1 was not successful",
                       "Fail-Enabling 12V Port 1 was not successful"]

    ##Test Port 2
    #Enable switch port C
    if(enableDisable(x2,mbRetries,"12V_C_OF","12V Port 2",1)):
        logging.debug("Sensor Booting...")
        time.sleep(5)#Give the sensor time to boot
        port2Status = sensorTest(x2,mbRetries,"RS232CComTest")#Call function to test communication on Port 2
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

#Test the serial flash chip
def testSerialFlash(GPIO,pinDict,x2,mbRetries):
    return ["Test not implemented"]

#Test that the system current is reading correctly
def testSysCur(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",-999999]

    #Read system current
    logging.debug("\nReading the system current...")
    readResult = mbReadFloatRetries(x2,Reg.mbReg["SysCur"][0],Reg.mbReg["SysCur"][1],retries=mbRetries)
    if(readResult):
        curr=readResult[0]
        currentLevel=valueRangeCheck(20,7,curr)
    else:
        logging.debug("The read was not successful")
        return ["Fail-The Modbus read failed",-999999]

    return [currentLevel[1],curr]

#Test trigger lines
def testTriggers(GPIO,pinDict,x2,mbRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful"]

    #Test the trigger lines are correct
    logging.debug("\nTesting Trigger 1...\n")
    trigger1 = triggerLineTest(GPIO,pinDict,x2,mbRetries,"Trigger1_OF","Trigger 1","TRIGGER1")
    logging.debug("\nTesting Trigger 2...\n")
    trigger2 = triggerLineTest(GPIO,pinDict,x2,mbRetries,"Trigger2_OF","Trigger 2","TRIGGER2")

    return [trigger1, trigger2]

#Test the Wi-Fi module is operating correctly
def testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries):
    logging.debug("Module Start")
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")

    #Enable the 3.3V SEPIC
    if(enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)== False):
        return ["Fail-Enabling the 3.3V SEPIC was not successful",
                "Fail-Enabling the 3.3V SEPIC was not successful"]
    #Enable the Wi-Fi Module
    if(enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",1)== False):
        return ["Fail-Enabling the Wi-Fi Module was not successful",
                "Fail-Enabling the Wi-Fi Module was not successful"]

    logging.debug("Waiting for Wi-Fi to boot fully before proceeding...")
    time.sleep(8)#Need to delay until Wi-Fi is fully booted and done communicating to K64
    
    #Search for Wi-Fi network name
    networkStatus=wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2)

    #Enable the Wi-Fi LEDs
    logging.debug("\nTesting the Wi-Fi LEDs...")
    [commStatusValue1,commStatus1]=checkStatus(x2,mbRetries,"WiFiComLEDTest","Wi-Fi LED Enable Write")

    #Check if LEDs were enabled
    done=False
    while not(done):
        LEDUserInput = input("Did all 4 Wi-Fi LEDs come on? (y/n): ")
        if(LEDUserInput == "y" or LEDUserInput == "Y"):
            logging.info("\nSuccess - You indicated that the LEDs were enabled\n")
            LEDStatus = "Pass"
            done=True
        elif (LEDUserInput == "n" or LEDUserInput == "n"):
            logging.info("\nFailure -  You indicated that the LEDs were not all enabled\n"
                  "This could mean no communication to Wi-Fi module or LEDs not connected correctly\n")
            LEDStatus = "Fail-All LEDs were not turned on"
            done=True
        else:
            logging.info("\nYou must enter y or n. Try again.\n")
            done=False

    #Disable Wi-Fi Module
    enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",0)

    return [networkStatus,LEDStatus]

#Test a trigger line
def triggerLineTest(GPIO,pinDict,x2,mbRetries,mbDictName,clearText,IOName):

    #Enable Trigger
    enableDisable(x2,mbRetries,mbDictName,clearText,1)

    #Read RPi IO line
    onStatus=GPIO.input(pinDict[IOName])
    logging.debug("The trigger read status is %s\n",onStatus)

    #Disable Trigger
    enableDisable(x2,mbRetries,mbDictName,clearText,0)

    #Read RPi IO line
    offStatus=GPIO.input(pinDict[IOName])
    logging.debug("The trigger read status is %s",offStatus)

    #Test Reasults
    if(onStatus == 1):
        if (offStatus == 0):
            logging.debug("The trigger works correctly")
            return "Pass"
        else:
            logging.debug("The trigger operation failed in the off state")
            return "Fail-Off status was "+str(offStatus)
    else:
        if(offStatus == 0):
            logging.debug("The trigger operation failed in the on state")
            return "Fail-On status was "+str(onStatus)
        else:
            logging.debug("The trigger operation failed in the on and off state")
            return ("Fail-On status was "+str(onStatus)+
                    " and Off status was "+str(offStatus))

#Test if a read voltage falls in a certain range
def valueRangeCheck(level,threshold,read):
    #Expected value, tolerance, input to test
    
    logging.debug("Checking if reading is in range...")
    if (read > level-threshold):
        if (read < level+threshold):
            logging.debug("Reading is in range. It is %.3f",read)
            return [True,"Pass"]
        else:
            logging.debug("Reading is too high. It is %.3f",read)
            return [False,"Fail-Reading high"]
    else:
        logging.debug("Reading is too low. It is %.3f",read)
        return [False,"Fail-Reading low"]

#Search for a specified Wi-Fi network
def wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2):  
    logging.debug("Looking for an X2 Wi-Fi network...")
    for i in range(0,wifiRetries):
        ssids=[cell.ssid for cell in Cell.all('wlan0')]
        logging.debug("\nList of all networks found: ")
        for value in ssids: #loop through and print found network names
            logging.debug(value)
        for ssid in ssids: #loop through found networks and scan for SSID
            if (wifiNetwork in ssid):
                done=True
                logging.debug("Attempt %d of %d was successful",i+1,wifiRetries)
                logging.debug("Found network: %s",ssid)
                break
            else:
                done=False
        if(done):
            logging.debug("Successfully found the Wi-Fi network\n")
            return "Pass"
        else:
            logging.debug("Failed to find a network with %s in it on attempt %d of %d", wifiNetwork, i+1, wifiRetries)
            if(i+1<wifiRetries):
                logging.debug("Waiting %d seconds and retrying...",sleepSec)
                time.sleep(sleepSec)
            else:
                logging.debug("Failed to find X2 network\n")
                return "Fail-Network not found"

#This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')
            

if __name__ == "__main__":    
    main()
        
