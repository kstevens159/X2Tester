#
# @file		        : FirstAttempt.py
# Project		: X2
# Author		: Kevin Stevens
# Created on	        : Jun 14, 2016
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
#	This script is for use on a Raspberry Pi 3 to test the X2 Main
#   board PCB.
# 
# Usage:
#   
#
# Revision Log:
# --------------------------------------------------------------------------
# MM/DD/YY hh:mm Who	Description
# --------------------------------------------------------------------------
# 06/14/16 16:30 KCS	Created
# --------------------------------------------------------------------------
#
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import serial
import logging
from datetime import datetime
import time
import sys

def main():
    mbAddress = 252
    baud = 19200
    comPort = '/dev/ttyUSB0'

    mb = ModbusClient(method='rtu', port=comPort, baudrate=baud, stopbits=serial.STOPBITS_ONE, parity=serial.PARITY_NONE, bytesize=serial.EIGHTBITS, timeout=3)

    connection = mb.connect()

    if connection == False:
        print "Connection failed\n"
        quit()
    else:
        print "Connection successful\n"

    TestCommunication(mb, mbAddress)

##    while(True):
##        try:
##            # Start DAQ and poll for status
##            DaqTest(mb, mbAddress)
##            time.sleep(60 * 7)
##            TestWaveReading(mb, mbAddress)
##        except:
##            print "Unexepcted error\n"
##
##def DaqTest(mb, mbAddress):
##    TestStartDaq(mb, mbAddress)
##    TestStartDaq(mb, mbAddress)
##    TestStartDaq(mb, mbAddress)
##    
##    for i in range(15):
##        DaqStatusTest(mb, mbAddress)
##    
##def DaqStatusTest(mb, mbAddress):
##    time.sleep(30)
##    TestDaqStatus(mb, mbAddress)
##    TestDaqSecondsLeft(mb, mbAddress)
##    TestDaqDataPointsCollected(mb, mbAddress)
##    TestMagReading(mb, mbAddress)
##    sys.stdout.flush()

# Test communication by reading address 
def TestCommunication(mb, mbAddress):
    print "\n==================="
    print str(datetime.now())
    print "Testing reading & writing Modbus address"

    readResult1 = ReadRegisters(mb, mbAddress, 0x1000, 1) #Read initial value

    if(readResult1.registers == [1]): #if address is already 1
        add=[2]
        writeResult = WriteRegisters(mb, mbAddress, 0x1000, add) #write address 2
    else: #otherwise
        add=[1]
        writeResult = WriteRegisters(mb, mbAddress, 0x1000, add) #write address 1

    readResult2 = ReadRegisters(mb, mbAddress, 0x1000, 1) #read the newly written address

    print(writeResult)
    print(readResult2)
    
    if(readResult2 and writeResult and writeResult.function_code < 0x80 and readResult2.function_code < 0x80 and readResult2.registers == add):
        print "Reading/writing address succeeded"
    else:
        print "Reading/writing address failed"
    
    print "===================\n"

    if(add==[2]):
        writeResult = WriteRegisters(mb, mbAddress, 0x1000, [1]) #write address 1 if it got set to 2
    
    sys.stdout.flush()
    
##def TestLocationAndDate(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Testing location and date"
##
##    readResult = ReadRegisters(mb, mbAddress, 0x3001, 9)
##    newVal =  [16927, 8607, 49831, 64705, 17490, 32768, 12, 2, 2016]
##    writeResult = WriteRegisters(mb, mbAddress, 0x3001, newVal)
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x3001, 9)
##    
##    if readResult and writeResult and writeResult.function_code < 0x80 and readResult.function_code < 0x80 and readResult.registers == newVal:
##        print "Location and date is working"
##    else:
##        print "Location and date failed"
##    
##    print "===================\n"
##    sys.stdout.flush()
##
##def TestWaveReading(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Testing wave reading"
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x3024, 30)
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestStartDaq(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Starting data acquisition"
##    
##    writeResult = WriteRegisters(mb, mbAddress, 0x300A, [1])
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestStopDaq(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Aborting data acquisition"
##    
##    writeResult = WriteRegisters(mb, mbAddress, 0x300A, [0])
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestDaqStatus(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Getting DAQ status (running or not)"
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x300A, 1)
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestDaqSecondsLeft(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Getting number of seconds left in DAQ"
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x3042, 1)
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestDaqDataPointsCollected(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Getting number of data points collected for DAQ"
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x3043, 1)
##    
##    print "===================\n"
##    sys.stdout.flush()
##    
##def TestMagReading(mb, mbAddress):
##    print "\n==================="
##    print str(datetime.now())
##    print "Getting mag reading"
##    
##    readResult = ReadRegisters(mb, mbAddress, 0x3045, 14)
##    
##    print "===================\n"
##    sys.stdout.flush()

def ReadRegisters(mbClient, mbAddress, startingRegister, numRegisters):
##    time.sleep(3)
    print "--Reading %d registers starting at register 0x%x" % (numRegisters, startingRegister)
    result = mbClient.read_input_registers(startingRegister, count=numRegisters, unit=mbAddress)
    
    if result is None:
        print "--Timeout"
        sys.stdout.flush()
        ReadDummyRegister(mbClient, mbAddress)
        return False
    else:
        if result.function_code >= 0x80:
            print "MB Exception: 0x%x" % result.exception_code
        else:
            if hasattr(result, 'registers'):
                print "--Read result: %s" % result.registers
            else:
                print result
        ReadDummyRegister(mbClient, mbAddress)
        sys.stdout.flush()
        return result
        
def ReadDummyRegister(mbClient, mbAddress):
    result = mbClient.read_input_registers(0xfff0, count=1, unit=mbAddress)
    
def WriteRegisters(mbClient, mbAddress, startingRegister, registerValues):
##    time.sleep(3)
    print "--Writing %s to register 0x%x" % (registerValues, startingRegister)
    result = mbClient.write_registers(startingRegister, registerValues, unit=mbAddress)
    
    if result is None:
        print "--Timeout"
        sys.stdout.flush()
        return False
    else:
        if result.function_code >= 0x80:
            print result
            print "MB Exception: 0x%x" % result.exception_code
        sys.stdout.flush()
        return result

if __name__ == "__main__":
    main()
