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
#     { "Key"               :[(Register #), (# of Registers),  (Function Code) ]
mbReg={ "Add"               :[0x1000,              1,                  4       ]#Reg1:Address
        ,"RTCBAT_V"         :[0x750E,              2,                  16      ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"SetTime"          :[0x701C,              4,                  16      ]#Reg1:Top of UTC Time; Reg2: Bottom of UTC Time; Reg3: Top of TZ Offset; Reg4: Bottom of TZ Offset
        ,"ReadTime"         :[0x701C,              4,                  4       ]#Reg1:Top of UTC Time; Reg2: Bottom of UTC Time; Reg3: Top of TZ Offset; Reg4: Bottom of TZ Offset
        ,"33SEPIC_OF"       :[0x7500,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"VCC33_V"          :[0x750C,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"SDTest"           :[0x7524,              1,                  4       ]#Reg1: 0=write/read fail; 1=write/read success
        ,"PriPwr_V"         :[0x7510,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"SecPwr_V"         :[0x7512,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"BakPwr_V"         :[0x7514,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"Valid"            :[0x751C,              1,                  4       ]#Reg1: Bit mask(Bit0=Valid1;Bit1=Valid2;Bit2=Valid3) [EX. 0b000=All off; 0b001=Valid1 on; 0b011=Valid1&2 on; 0b111=All on]
        ,"PPP_Dis"          :[0x750B,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"SysCur"           :[0x7518,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"12SEPIC_OF"       :[0x7501,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"12VSen_V"         :[0x7516,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"5VLDO_OF"         :[0x7502,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"12V_A_OF"         :[0x7503,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"12V_B_OF"         :[0x7504,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"12V_C_OF"         :[0x7505,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"12V_D_OF"         :[0x7506,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"SenCur"           :[0x751A,              2,                  4       ]#Reg1: Upper word of float; Reg2: Lower word of float
        ,"PriPwr_OF"        :[0x7507,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"WiFiPwr_OF"       :[0x7508,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"WiFiComLEDTest"   :[0x7525,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success - Each send also toggles LEDs on/off
        ,"RS485ComTest"     :[0x752B,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success
        ,"RS232AComTest"    :[0x752C,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success
        ,"RS232BComTest"    :[0x752D,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success
        ,"RS232CComTest"    :[0x752E,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success
        ,"SDI12ComTest"     :[0x752F,              1,                  4       ]#Reg1: 0=comm. fail; 1=comm. success
        ,"MagIntTest0"      :[0x7527,              2,                  4       ]#Reg1: Top of UTC time since last mag; Reg2: Bottom of UTC time since last mag
        ,"MagIntTest1"      :[0x7529,              2,                  4       ]#Reg1: Top of UTC time since last mag; Reg2: Bottom of UTC time since last mag
        ,"ReadInternalSens" :[0x751D,              6,                  4       ]#Reg1: Upper word of pressure float; Reg2: Lower word of pressure float; Reg1: Upper word of temp float; Reg2: Lower word of temp float; Reg1: Upper word of humidity float; Reg2: Lower word of humidity float; 
        ,"K64LED"           :[0x7526,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"Trigger1_OF"      :[0x7509,              1,                  16      ]#Reg1: 0=off; 1=on
        ,"Trigger2_OF"      :[0x750A,              1,                  16      ]#Reg1: 0=off; 1=on

        ,"RTU50SysCur"      :[0x1000,              1,                  4       ]
        ,"RTU33SysCur"      :[0x1000,              1,                  4       ]
        ,"EthPwr_OF"        :[0x1000,              1,                  4       ]
        ,"ReadTrigger1"     :[0x1000,              1,                  4       ]
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
