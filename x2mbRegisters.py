#
# @file		        : x2mbRegisters.py
# Project		: S500/DL100
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
#	This 
# 
# Usage:
#   Called from the X2 PCB Tester Code
#
# Revision Log:
# --------------------------------------------------------------------------
# MM/DD/YY hh:mm Who	Description
# --------------------------------------------------------------------------
# 01/13/16 16:30 AJF	Created
# --------------------------------------------------------------------------
#

#Dictionary of various Modbus Registers for interfacing to the X2
#     {"Key"     :   [(Register #), (Number of Registers)]
mbReg={"Add"     :   [0x1000,1],
       "ex"      :   [0x1020,2]
       }
#To get the register number
#mbReg["KEY"][0]
##print(mbReg["Add"][0])

#To get the number of registers
#mbReg["KEY"][1]
##print(mbReg["Add"][1])

