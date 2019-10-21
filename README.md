# PyBmr
Python library for communication with BMR HC64 Heating Controller units

## Install:

```
python3 -m pip install pybmr
```

## Usage examples:

### Initiate library:
```
from pybmr import pybmr

bmr = pybmr.Bmr("192.168.1.5","passwordForBmrWebUserInterface")
```

### Get status of your unit with human readable identifications (if available):
```
status = bmr.getStatus()
if(status == False):
    exit("Authentication failed")

for id, value in status.items():
    print(atrea.getRoom(id) + ":" + value)
```

## Technical details
### Sample requests
```
curl -X POST http://192.168.1.menu.html -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -d 'loginName=C327&passwd=242136'
curl -X POST http://192.168.1.5/numOfRooms -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -d 'param=+'
curl -X POST -Si http://192.168.1.5/wholeRoom -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' -d 'param=3'
```

### Syntax returned from BMR
```
1Pokoj 202 v  021.7+12012.0000.000.0000000000
````

# Upload
```
python3 setup.py sdist bdist_wheel
python3 -m twine upload  dist/*
```