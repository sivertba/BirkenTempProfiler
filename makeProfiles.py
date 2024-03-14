import os
durations = [ # HH:MM
    (3,30),
    (4,0),
    (4,30),
    (5,0),
    (5,30),
    (6,0),    
]

StartTimes = [ # HH:MM, Assuming 2024-03-16
    ("07","30"),
    ("08","00"),
    ("08","30"),
    ("09","00"),
    ("09","30"),
]

for dur in durations:
    for st in StartTimes:

        cmd = "python3 birkentempprofiler.py -r 'rennet' "
        cmd += "-s '2024-03-16T" + st[0] + ":" + st[1] + ":00' "
        cmd += "-t " + str(dur[0]) + " -m " + str(dur[1])
        print(cmd)
        os.system(cmd)
        newName = f"temperatureProfile_{st[0]}_{st[1]}_T_{dur[0]}_{dur[1]}.html"
        os.rename("temperatureProfile.html", newName)

