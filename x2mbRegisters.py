#
# @file		        : x2mbRegisters.py
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
#	This file holds all the modbus register information for the various
#       required tests and data requests. This allows for a more readable
#       code file by using names instead of just register numbers.
# 
# Usage:
#   Called from the X2 PCB Tester Code
#
# Revision Log:
# --------------------------------------------------------------------------
# MM/DD/YY hh:mm Who	Description
# --------------------------------------------------------------------------
# 01/13/16 16:30 KCS	Created
# --------------------------------------------------------------------------
#

#Dictionary of various Modbus Registers for interfacing to the X2
#     { "Key"            :[(Register #), (# of Registers),  (Function Code) ]
mbReg={ "Add"            :[0x1000,              1,                  4       ]
        ,"RTCBAT"        :[0x1000,              1,                  4       ]
        ,"SetTime"       :[0x1000,              1,                  4       ]
        ,"ReadTime"      :[0x1000,              1,                  4       ]
        ,"33SEPIC_OF"    :[0x1000,              1,                  4       ]
        ,"VCC33_V"       :[0x1000,              1,                  4       ]
        ,"EETest"        :[0x1000,              1,                  4       ]
        ,"SDTest"        :[0x1000,              1,                  4       ]
        ,"PriPwr_V"      :[0x1000,              1,                  4       ]
        ,"SecPwr_V"      :[0x1000,              1,                  4       ]
        ,"BakPwr_V"      :[0x1000,              1,                  4       ]
        ,"Valid1"        :[0x1000,              1,                  4       ]
        ,"Valid2"        :[0x1000,              1,                  4       ]
        ,"Valid3"        :[0x1000,              1,                  4       ]
        ,"PPP_Dis"       :[0x1000,              1,                  4       ]
        ,"SysCur"        :[0x1000,              1,                  4       ]
        ,"12SEPIC_OF"    :[0x1000,              1,                  4       ]
        ,"12VSen_V"      :[0x1000,              1,                  4       ]
        ,"5VLDO_OF"      :[0x1000,              1,                  4       ]
        ,"12V_A_OF"      :[0x1000,              1,                  4       ]
        ,"12V_B_OF"      :[0x1000,              1,                  4       ]
        ,"12V_C_OF"      :[0x1000,              1,                  4       ]
        ,"12V_D_OF"      :[0x1000,              1,                  4       ]
        ,"SenCur"        :[0x1000,              1,                  4       ]
        ,"PriPwr_OF"     :[0x1000,              1,                  4       ]
        ,"WiFiPwr_OF"    :[0x1000,              1,                  4       ]
        ,"WiFiComTest"   :[0x1000,              1,                  4       ]
        ,"RS485ComTest"  :[0x1000,              1,                  4       ]
        ,"RS232ComTest"  :[0x1000,              1,                  4       ]
        ,"SDI12ComTest"  :[0x1000,              1,                  4       ]
        ,"MagIntTest"    :[0x1000,              1,                  4       ]
        ,"ReadPress"     :[0x1000,              1,                  4       ]
        ,"ReadTemp"      :[0x1000,              1,                  4       ]
        ,"ReadHum"       :[0x1000,              1,                  4       ]
        ,"K64LED"        :[0x1000,              1,                  4       ]
        ,"TILED"         :[0x1000,              1,                  4       ]
        ,"Trigger1_OF"   :[0x1000,              1,                  4       ]
        ,"Trigger2_OF"   :[0x1000,              1,                  4       ]

        ,"RTU50SysCur"   :[0x1000,              1,                  4       ]
        ,"RTU33SysCur"   :[0x1000,              1,                  4       ]
        ,"EthPwr_OF"     :[0x1000,              1,                  4       ]
        ,"ReadTrigger1"  :[0x1000,              1,                  4       ]
       }
#To get the register number
#mbReg["KEY"][0]
##print(mbReg["Add"][0])

#To get the number of registers
#mbReg["KEY"][1]
##print(mbReg["Add"][1])

#To get the function code
#mbReg["KEY"][2]
##print(mbReg["Add"][2])
