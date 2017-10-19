import json
import datetime
import os

import requests
import platform
import time
import c8y_http
import util.utils as utils

C8Y_BOOTSTRAP_AUTH = ('management/devicebootstrap', 'Fhdt1bb1f')

AVAILABILITY_REQUIRED_INTERVAL = 60 # minutes


class C8yDevice():
    ''' Handles Cumulocity lifecycle
    '''

    def __init__(self, url, tenant, serial=utils.get_mac_string(), persist_state=True):

        self.name = "Generic Agent"
        self.type = "Generic UTEE type"
        self.serial_no = serial
        self.tenant = tenant
        self.cumu_url = url
        self.auth = {}
        self.child_ids = []
        self.device_info = {}

        self.CREDENTIALS_FILE = "./" + self.serial_no + "/credentials.json"
        self.DEVICE_JSON = "./" + self.serial_no + "/device.json"

    def bootstrap(self):
        # 1. Acquire Credentials
        self.auth = self.get_credentials()
        self.update_c8y_inventory()

    def update_c8y_inventory(self):
        # Is Device registered?
        if not self.device_registered():
            print "[i] Registering self..."
            response = self.create_device()
            if response is not None:
                self.device_info = response.json()
                utils.write_to_file(response.json(), self.DEVICE_JSON)
                self.register_device()
        else:
            print "[i] Device already registered..."
            self.device_info = utils.load_json_file(self.DEVICE_JSON)
            # self.update_device_in_inventory()

    # See if local credentials exist, fetch new credentials from Cumulocity  otherwise
    def get_credentials(self):
        if not os.path.exists(self.CREDENTIALS_FILE):
            while True:
                response = self.request_credentials()
                if response is not None:
                    print "[!] Writing Device credentials to file... ", self.CREDENTIALS_FILE
                    utils.write_to_file(response.json(), self.CREDENTIALS_FILE)
                    break
                else:
                    print "[d] Trying again in 3 seconds..."
                    time.sleep(3)
        else:
            print "[i] Using existing credentials file: ", self.CREDENTIALS_FILE

        # create Auth object from file
        return self.load_auth_from_file()

    def load_auth_from_file(self):
        credentials = utils.load_json_file(self.CREDENTIALS_FILE)
        return (self.tenant + "/" + credentials["username"], credentials["password"])

    def request_credentials(self):
        request_url = self.cumu_url + 'devicecontrol/deviceCredentials'
        headers = c8y_http.HEADER_DEVICECREDENTIALS_JSON

        payload = { "id": self.serial_no }

        resp = requests.post(request_url,
                             auth=C8Y_BOOTSTRAP_AUTH,
                             data=json.dumps(payload),
                             headers=headers)

        if resp.status_code == 201:
            print "[i] Received Device credentials: ", resp.text
            return resp

        elif resp.status_code == 404:
            print "[e] 404 - Unable to get credentials. " \
                  "Have you registered and accepted the new device (id: "+ self.serial_no + ") in Cumulocity Device Management?"
        else:
            print "[e] Unable to get credentials: ", resp.status_code, resp.json()
        return None


    def is_device_registered(self):
        request_url = self.cumu_url + 'identity/externalIds/c8y_Serial/' + self.serial_no
        resp = requests.get(request_url, auth=self.auth)
        return resp.status_code == 200

    def add_sample_operation(self):
        request_url = self.cumu_url + 'inventory/managedObjects/' + self.device_info["id"]
        headers = c8y_http.HEADER_MANAGEDOBJECT_JSON

        payload = {
            "c8y_SupportedOperations": ["c8y_Restart"]
        }

        requests.put(request_url, auth=self.auth, headers=headers, data=payload)


    def create_device(self):
        request_url = self.cumu_url + 'inventory/managedObjects'
        headers = c8y_http.HEADER_MANAGEDOBJECT_JSON

        data = {
            "name": self.name,
            "type": self.type,
            "c8y_IsDevice": {},
            "com_cumulocity_model_Agent": {},
            "c8y_RequiredAvailability": {"responseInterval": AVAILABILITY_REQUIRED_INTERVAL },
            "c8y_Hardware": {
                "revision": platform.version(),
                "model": platform.platform(),
                "serialNumber": self.serial_no
            }
        }

        resp = requests.post(request_url, auth=self.auth, data=json.dumps(data), headers=headers)

        if resp.status_code == 201:
            print "[i] Created Device: ", resp.text
            return resp

        else:
            print "[e] Unable to create Device: ", resp.status_code, resp.json()
            return None


    def device_registered(self):
        request_url = self.cumu_url + 'identity/externalIds/c8y_Serial/' + self.serial_no
        resp = requests.get(request_url, auth=self.auth)
        return resp.status_code == 200


    def register_device(self):
        request_url = self.cumu_url + 'identity/globalIds/' + self.device_info["id"] + '/externalIds'
        headers = c8y_http.HEADER_EXTERNAL_ID_JSON

        data = {
            "type": "c8y_Serial",
            "externalId": self.serial_no
        }

        resp = requests.post(request_url, auth=self.auth, data=json.dumps(data), headers=headers)
        if resp.status_code == 201:
            print "[i] Registered Device: ", resp.text
        else:
            print "[e] Unable to register Device: ", resp.status_code
            print resp.text

    def send_measurement(self, data):
        request_url = self.cumu_url + "/measurement/measurements"
        headers = c8y_http.HEADER_MEASUREMENT_JSON

        resp = requests.post(request_url, auth=self.auth, data=json.dumps(data), headers=headers)
        if resp.status_code == 201:
            print "[i] Sent measurement: ", resp.text
        else:
            print "[e] Unable to send measurement: ", resp.status_code
            print resp.text


    ## todo remove this next method
    def child_send_measurement(self, value):
        request_url = self.cumu_url + "/measurement/measurements"
        headers = c8y_http.HEADER_MEASUREMENT_JSON

        data = {
            "c8y_TemperatureMeasurement": {
                "T": {
                    "value": value,
                    "unit": "C"
                }
            },

            "time": datetime.datetime.utcnow().isoformat(),
            "source": {"id": str(self.child_ids[0])},
            "type": "c8y_TemperatureMeasurement"
        }


        resp = requests.post(request_url, auth=self.auth, data=json.dumps(data), headers=headers)
        if resp.status_code == 201:
            print "[i] Sent measurement: ", resp.text
        else:
            print "[e] Could not send measurement: ", resp.text

    ''' Create Child Device and link it to this device '''
    def spawn_child_device(self, name, supported_measurements):
        url = self.cumu_url + "/inventory/managedObjects"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "name": name,
            "c8y_SupportedMeasurements": supported_measurements
        }

        resp = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        if resp.status_code == 201:
            child_id = resp.json()["id"]
            print "[i] Created child: ", child_id
            self.child_ids.append(child_id)
        else:
            print "[e] Error creating child: ", resp.text
            return


        # Link child with this
        url = self.cumu_url + "/inventory/managedObjects/" + self.device_info["id"] + "/childDevices"
        data = { "managedObject": {"id": child_id} }
        resp = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        if resp.status_code == 201:
            print "[i] Linked child: ", child_id
        else:
            print "[e] Error linking child: ", resp.text

    def get_children(self):
        url = self.device_info["childDevices"]["self"]
        return requests.get(url, auth=self.auth)

    def update_deviceinfo(self):
        url = self.device_info["self"]
        response = requests.get(url, auth=self.auth)
        return response

    def update_device_in_inventory(self):
        url = self.device_info["self"]
        headers = c8y_http.HEADER_MANAGEDOBJECT_JSON
        data = {
        }
        requests.put(url, data = data, auth=self.auth)







