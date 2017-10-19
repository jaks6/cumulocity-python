import datetime
import time
from random import random

from c8y import C8yDevice


class SimulatedSensor(C8yDevice):
    def __init__(self, url, tenant, serial):
        C8yDevice.__init__(self, url, tenant, serial)

    def send_temperature_measurement(self):
        data = {
            "c8y_TemperatureMeasurement": {
                "T": { "value": (random() * 10 + 15), "unit": "C" }
            },
            "time": datetime.datetime.utcnow().isoformat(),
            "source": {"id": str(self.device_info["id"])},
            "type": "c8y_TemperatureMeasurement"
        }
        self.send_measurement(data)


if __name__ == '__main__':

    sensor = SimulatedSensor(url="https://testing.iot.cs.ut.ee/", tenant="testing", serial="simulated1")
    sensor.name = "Temperature Sensor"
    sensor.type = "Python-Simulated Sensor"

    # Load credentials, update device in Cumulocity inventory
    sensor.bootstrap()

    # Send some measurements
    while True:
        sensor.send_temperature_measurement()
        time.sleep(2)