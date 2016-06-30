from wifi import Cell
import time

for i in range(0,5):
    ssids=[cell.ssid for cell in Cell.all('wlan0')]
    print(ssids)
    for ssid in ssids:
        if ("Zy" in ssid):
            done=True
            print("Successfully found network:",ssid)
            break
        else:
            done=False
            print("NO")
    if(done):
        break
    time.sleep(1)
