import os

durations = [(hh,mm) for hh in range(3,8) for mm in [45, 30, 15, 0] ]

# Assuming 2024-03-16
StartTimes = [ (str(hh), str(mm)) for hh in range(7,10) for mm in [45, 30, 15, 0] ]

for dur in durations:
    for st in StartTimes:

        hh = str(st[0])
        mm = str(st[1])

        if len(hh) == 1:
            hh = "0" + hh
        if len(mm) == 1:
            mm = "0" + mm

        cmd = "python3 birkentempprofiler.py -r 'rennet' "
        cmd += "-s '2024-03-16T" + hh + ":" + mm + ":00' "
        cmd += "-t " + str(dur[0]) + " -m " + str(dur[1])
        print(cmd)
        os.system(cmd)

        folderPath = "profiles"
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        newName = f"temperatureProfile_{hh}_{mm}_T_{dur[0]}_{dur[1]}.html"
        newName = os.path.join(folderPath, newName)
        os.rename("temperatureProfile.html", newName)

