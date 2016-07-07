import datetime
import struct

def splitInto16Bits(combined):

    rawSeparate=struct.unpack('>4H',struct.pack('>Q',combined))
    print(hex(rawSeparate[0]),hex(rawSeparate[1]),hex(rawSeparate[2]),hex(rawSeparate[3]))

    k=0
    separate=[]
    for i in range(0,4):
        if (rawSeparate[i] != 0):
            separate.append(rawSeparate[i])
            k=k+1
            
    return separate

def combineFrom16Bits(separate):

    combined = 0
    k=len(separate)
    for i in range(0,len(separate)):
        combined = combined + (separate[k-1]<<(16*i))
        k=k-1
        
    return combined

separateValues=[0x1234,0x5678,0x9ABC]
combinedValue=0x123456789ABCDEF0

separate = splitInto16Bits(combinedValue)
combineFrom16Bits(separateValues)


