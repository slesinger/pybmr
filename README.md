# PyBmr

Python library for communication with BMR HC64 Heating Controller units.

Product website: 
 - https://bmr.cz/produkty/regulace-topeni/rnet
 - https://bmr.cz/produkty/regulace-topeni/rt64

## Install:

```
python3 -m pip install pybmr
```

## Usage examples

### Create connection

```
from pybmr import pybmr

bmr = pybmr.Bmr("http://192.168.1.5/", "username, "password")
```

### Circuits

Get number of circuits:

```
numCircuits = bmr.getNumCircuits()
```

Load circuit status:

```
circuit = bmr.getCircuit(0)
print(f"Circuit {circuit['name']}: temperature is {circuit['temperature']} °C, target temperature is {circuit['target_temperature']} °C")
```

Load circuit schedules (what schedule is assigned to what day). It is possible to assign a different schedule for up to 21 days.

```
circuit_schedules = bmr.getCircuitSchedules(0)
print(f"Circuit 0 schedule for the first day is {circuit_schedules['day_schedules'][0]}")
```

Save circuit schedules:

```
bmr.setCircuitSchedules(0, [0, 8])
```


### Schedules

Load schedules:

```
schedules = bmr.getSchedules()
print(schedule[0])  # Print the name of first schedule
```

Get schedule details:

```
schedule = bmr.getSchedule(0)
print(f"Schedule {schedule['name']} has timetable {schedule['timetable']}")
```

Save schedule:

```
bmr.setSchedule(0, "New schedule name", [("00:00", 21), ("06:00", 23), ("21:00", 21)])
```

Delete schedule:

```
bmr.deleteSchedule(0)
```

### Summer mode

Get summer mode:

```
if bmr.getSummerMode():
    print("Summer mode is ON")
else:
    print("Summer mode is OFF")
```

Set summer mode:

```
bmr.setSummerMode(True):
```

Load summer mode assignments (which circuits will be affected by turning the
summer mode on):

```
assignments = bmr.getSummerModeAssignments()
for circuit_id, value in enumerate(assignments):
    if value:
        print(f"Circuit {circuit_id} is assigned to summer mode.")
    else:
        print(f"Circuit {circuit_id} is NOT assigned to summer mode.")
```

Add circuits to summer mode:

```
bmr.setSummerModeAssignments([0, 1, 2], True)
```

Remove circuits from summer mode:

```
bmr.setSummerModeAssignments([0, 1, 2], False)
```

### Low mode

Get low mode:

```
low_mode = bmr.getLowMode()
if low_mode['enabled']:
  print(f"Low mode is turned ON since {low_mode['start_date']}, target temperature is {low_mode['temperature']}")
  if low_mode['end_date']:
    print(f"It will be turned off automatically on {low_mode['end_date']}")
```

Turn the low mode ON, set temperature to 18°C:

```
bmr.setLowMode(True, 18)
```

Turn the low mode ON and let it turn OFF automatically after 3 days:

```
bmr.setLowMode(True, 18, datetime.now(), datetime.now() + timedelta(days=3))
```

Turn the low mode OFF:

```
bmr.setLowMode(False)
```

Load low mode assignments (which circuits will be affected by turning the
low mode on):

```
assignments = bmr.getLowModeAssignments()
for circuit_id, value in enumerate(assignments):
    if value:
        print(f"Circuit {circuit_id} is assigned to low mode.")
    else:
        print(f"Circuit {circuit_id} is NOT assigned to low mode.")
```

Add circuits to low mode:

```
bmr.setLowModeAssignments([0, 1, 2, 6, 7, 8], True)
```

Remove circuits from low mode:

```
bmr.setLowModeAssignments([0, 1, 2, 6, 7, 8], False)
```

### HDO

Load HDO status:

```
hdo = bmr.getHDO()
if hdo:
  print("HDO is currently ON")
else:
  print("HDO is currently OFF")
```

## Backup of BMR Controler Unit Configuration

There is a CLI tool that can be used to backup configuration of actual BMR Controler Unit. It can be used in automations or just as a remote management tool. For more information refer to https://github.com/dankeder/bmrcli
