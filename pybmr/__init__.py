# Author: Honza Slesinger
# Tested with:
#    BMR HC64 v2013

from datetime import datetime, date
import re

import requests


class Bmr:
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

    def getNumCircuits(self):
        """ Get the number of heating circuits.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/numOfRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": "+"}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return int(response.text)

    def loadCircuit(self, circuit_id):
        """ Get circuit status.

            Raw data returned from server:

              1Pokoj 202 v  021.7+12012.0000.000.0000000000

            Byte offsets of:
              POS_ENABLED = 0
              POS_NAME = 1
              POS_ACTUALTEMP = 14
              POS_REQUIRED = 19
              POS_REQUIREDALL = 22
              POS_USEROFFSET = 27
              POS_MAXOFFSET = 32
              POS_S_TOPI = 36
              POS_S_OKNO = 37
              POS_S_KARTA = 38
              POS_VALIDATE = 39
              POS_LOW = 42
              POS_LETO = 43
              POS_S_CHLADI = 44
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/wholeRoom".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"param": circuit_id}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))

        match = re.match(
            r"""
                (?P<enabled>.{1})                  # Whether the circuit is enabled
                (?P<name>.{13})                    # Name of the circuit
                (?P<temperature>.{5})              # Current temperature
                (?P<target_temperature_str>.{3})   # Target temperature (string)
                (?P<target_temperature>.{5})       # Target temperature (float)
                (?P<user_offset>.{5})              # Current temperature offset set by user
                (?P<max_offset>.{4})               # Max temperature offset
                (?P<heating>.{1})                  # Whether the circuit is currently heating
                (?P<window_heating>.{1})
                (?P<card>.{1})
                (?P<warning>.{3})                  # Warning code
                (?P<low_mode>.{1})                 # Whether the circuit is assigned to low mode and low mode is active
                (?P<summer_mode>.{1})              # Whether the circuit is assigned to summer mode and summer mode
                                                   # is active
                (?P<cooling>.{1})                  # Whether the circuit is cooling (only water-based circuits)
                """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        room_status = match.groupdict()

        # Sometimes some of the values are malformed, i.e. "00\x00\x00\x00" or "-1-1-"
        result = {
            "id": circuit_id,
            "enabled": bool(int(room_status["enabled"])),
            "name": room_status["name"].rstrip(),
            "temperature": None,
            "target_temperature": None,
            "user_offset": None,
            "max_offset": None,
            "heating": bool(int(room_status["heating"])),
            "warning": int(room_status["warning"]),
            "cooling": bool(int(room_status["cooling"])),
            "low_mode": bool(int(room_status["low_mode"])),
            "summer_mode": bool(int(room_status["summer_mode"])),
        }

        try:
            result["temperature"] = float(room_status["temperature"])
        except ValueError:
            pass

        try:
            result["target_temperature"] = float(room_status["target_temperature"])
        except ValueError:
            pass

        try:
            result["user_offset"] = float(room_status["user_offset"])
        except ValueError:
            pass

        try:
            result["max_offset"] = float(room_status["max_offset"])
        except ValueError:
            pass

        return result

    def auth(self):
        def bmr_hash(value):
            output = ""
            day = date.today().day
            for c in value:
                tmp = ord(c) ^ (day << 2)
                output = output + hex(tmp)[2:].zfill(2)
            return output.upper()

        url = "http://{}/menu.html".format(self.ip)
        data = {
            "loginName": bmr_hash(self.user),
            "passwd": bmr_hash(self.password),
        }
        response = requests.post(url, data=data)
        if "res_error_title" in response.text:
            return False
        return True

    def setTargetTemperature(self, temperature, mode_order_number, mode_name):
        self.auth()

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payloadstr = (
            "modeSettings="
            + str(mode_order_number).zfill(2)
            + mode_name.ljust(13, "+")
            + "00%3A00"
            + str(int(temperature)).zfill(3)
        )
        response = requests.post(
            "http://" + self.ip + "/saveMode", headers=headers, data=payloadstr
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    def getSummerMode(self):
        """ Return True if summer mode is currently activated.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/loadSummerMode".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(url, headers=headers, data="param=+")
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return response.text == "0"

    def setSummerMode(self, value):
        """ Enable or disable summer mode.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/saveSummerMode".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        payload = {"summerMode": "0" if value else "1"}
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    def loadSummerModeAssignments(self):
        """ Load circuit summer mode assignments, i.e. which circuits will be
            affected by summer mode when it is turned on.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/letoLoadRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(url, headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        try:
            return [bool(int(x)) for x in list(response.text)]
        except ValueError:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))

    def saveSummerModeAssignments(self, circuits, value):
        """ Assign or remove specified circuits to/from summer mode. Leave
            other circuits as they are.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        assignments = self.loadSummerModeAssignments()

        for circuit_id in circuits:
            assignments[circuit_id] = value

        url = "http://{}/letoSaveRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"value": "".join([str(int(x)) for x in assignments])}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    def getLowMode(self):
        """ Get status of the LOW mode.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/loadLows".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(url, headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        # The response is formatted as "<temperature><start_datetime><end_datetime>", let's parse it
        match = re.match(
            r"""
            (?P<temperature>\d{3})
            (?P<start_datetime>\d{4}-\d{2}-\d{2}\d{2}:\d{2})?
            (?P<end_datetime>\d{4}-\d{2}-\d{2}\d{2}:\d{2})?
            """,
            response.text,
            re.VERBOSE,
        )
        if not match:
            raise Exception("Server returned malformed data: {}. Try again later".format(response.text))
        low_mode = match.groupdict()
        result = {"enabled": low_mode["start_datetime"] is not None, "temperature": int(low_mode["temperature"])}
        if low_mode["start_datetime"]:
            result["start_date"] = datetime.strptime(low_mode["start_datetime"], "%Y-%m-%d%H:%M")
        if low_mode["end_datetime"]:
            result["end_date"] = datetime.strptime(low_mode["end_datetime"], "%Y-%m-%d%H:%M")
        return result

    def setLowMode(self, enabled, temperature=None, start_datetime=None, end_datetime=None):
        """ Enable or disable LOW mode. Temperature specified the desired
            temperature for the LOW mode.

            - If start_date is provided enable LOW mode indefiniitely.
            - If also end_date is provided end the LOW mode at this specified date/time.
            - If neither start_date nor end_date is provided disable LOW mode.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        if start_datetime is None:
            start_datetime = datetime.now()

        if temperature is None:
            temperature = self.getLowMode()["temperature"]

        url = "http://{}/lowSave".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {
            "lowData": "{:03d}{}{}".format(
                int(temperature),
                start_datetime.strftime("%Y-%m-%d%H:%M") if enabled and start_datetime else " " * 15,
                end_datetime.strftime("%Y-%m-%d%H:%M") if enabled and end_datetime else " " * 15,
            )
        }
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    def loadLowModeAssignments(self):
        """ Load circuit LOW mode assignments, i.e. which circuits will be
            affected by LOW mode when it is turned on.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/lowLoadRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(url, headers=headers, data={"param": "+"})
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return [bool(int(x)) for x in list(response.text)]

    def saveLowModeAssignments(self, circuits, value):
        """ Assign or remove specified circuits to/from LOW mode. Leave
            other circuits as they are.
        """
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        assignments = self.loadLowModeAssignments()

        for circuit_id in circuits:
            assignments[circuit_id] = value

        url = "http://{}/lowSaveRooms".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"value": "".join([str(int(x)) for x in assignments])}
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return "true" in response.text

    def get_mode_id(self, circuit_id):
        if circuit_id == None:
            return None

        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        payload = {"roomID": circuit_id}
        response = requests.post(
            "http://" + self.ip + "/roomSettings", headers=headers, data=payload
        )
        if response.status_code == 200:
            try:
                return int(response.content[2:4]) - 32
            except ValueError:
                return None

    # 230110-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    # 230109-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    # 23011013-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1
    def set_mode_id(self, circuit_id, mode_id):
        self.auth()
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}

        payload = {
            "roomSettings": str(circuit_id).zfill(2)
            + "01"
            + str(mode_id).zfill(2)
            + "-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1"
        }
        response = requests.post(
            "http://" + self.ip + "/saveAssignmentModes", headers=headers, data=payload
        )
        if response.status_code == 200:
            if response.content == "true":
                return True
            else:
                return False

    def loadHDO(self):
        if not self.auth():
            raise Exception("Authentication failed, check username/password")

        url = "http://{}/loadHDO".format(self.ip)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        response = requests.post(url, headers=headers, data="param=+")
        if response.status_code != 200:
            raise Exception("Server returned status code {}".format(response.status_code))
        return response.text == "1"
