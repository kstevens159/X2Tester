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

def main():

    ##############################
    ## Define program variables ##
    ##############################
    
    #Device Parameters
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

    #Power on X2
    powerOn(x2,mbRetries,GPIO,pinDict,"IO1")
    #Enable the 3.3V SEPIC
    enableDisable(x2,mbRetries,"33SEPIC_OF","3.3V SEPIC",1)
    #Enable the Wi-Fi Module
    enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",1)

    logging.debug("Waiting for Wi-Fi to boot fully before proceeding...")
    time.sleep(8)#Need to delay until Wi-Fi is fully booted and done communicating to K64

    for i in range(0,1000):

        logging.debug("\n\n\n"
                      "------------- ITTERATION START  -------------")
        logging.debug("------------- %s -------------",time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(time.time())))
        logging.debug("------------- Run %d -------------\n\n\n",i)

        #Enable the Wi-Fi Module
        enableDisable(x2,mbRetries,"WiFiPwr_OF","Wi-Fi Module",1) #Sent inside the loop to keep the Wi-Fi on (otherwise it sleeps)
        
        testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries)












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





#Test the Wi-Fi module is operating correctly
def testWifi(GPIO,pinDict,x2,mbRetries,wifiNetwork,wifiRetries):
    logging.debug("Module Start")
    
    
    #Search for Wi-Fi network name
    networkStatus=wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2)

#Search for a specified Wi-Fi network
def wifiNetworkSearch(wifiNetwork,wifiRetries,sleepSec=2):
    for k in range(0,3): #Sometimes this will fail if the system is trying to access at the same time
        try:
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
        except:
            time.sleep(2)
            logging.debug("Wi-Fi network resource busy on attempt %d of 3",k+1)
            pass
    else:
        return "Fail-RPi was using the Wi-Fi resource"

#This function replaces the standard minimalmodbus address range (0-247) with an extended range (0-255)
def _checkSlaveaddress(slaveaddress):
    SLAVEADDRESS_MAX=255
    SLAVEADDRESS_MIN=0
    minimalmodbus._checkInt(slaveaddress,SLAVEADDRESS_MIN,SLAVEADDRESS_MAX,description='slaveaddress')

if __name__ == "__main__":
    ############################################
    ## Setup global settings for the log file ##
    ############################################

    #Create custom logging level
    logging.IMPORTANT = 25
    logging.addLevelName(logging.IMPORTANT, "IMPORTANT")
    logging.Logger.important = lambda inst, msg, *args, **kwargs: inst.log(logging.IMPORTANT, msg, *args, **kwargs)
    logging.important = lambda msg, *args, **kwargs: logging.log(logging.IMPORTANT, msg, *args, **kwargs)

    log_level_console = logging.DEBUG #For NexSens Use

    #Set file logging settings
    log_level_file = logging.DEBUG #Always capture all to the log

    #Check if folder is there and if not make
    log_file_name = "/home/pi/Desktop/ProgramRun.log"

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

    ###############
    ## Call Main ##
    ###############
    main()
