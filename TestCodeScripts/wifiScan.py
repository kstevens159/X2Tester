from wifi import Cell
import time

searchString="X2 Logger"
retries=5
sleepSec = 10

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
        break
    else:
        print("Failed to find a network with", searchString, "in it on attempt", i+1, "of", retries)
        if(i+1<retries):
            print("Waiting", sleepSec, "seconds and retrying...")
            time.sleep(sleepSec)
        else:
            print("Failed to find network")
