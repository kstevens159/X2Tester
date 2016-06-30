from wifi import Cell
import time

searchString="Zy"

for i in range(0,5):
    ssids=[cell.ssid for cell in Cell.all('wlan0')]
    print(ssids)
    for ssid in ssids:
        if (searchString in ssid):
            done=True
            print("Successfully found network:",ssid)
            break
        else:
            done=False
    if(done):
        break
    else:
        print("Failed to find a network with", searchString, "in it on attempt", i+1)
        print("Waiting and retrying")
        time.sleep(10)
