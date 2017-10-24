import datetime
import json
import struct

import requests

from c8y import c8y_http
from modbus.Agent import Agent

CUMU_URL = "https://testing.iot.cs.ut.ee/"
TENANT_ID = "testing"

MODBUS_TEMPLATE = "./modbus.json"

def send_register_measurement(value, slave, register):
    request_url = agent.cumu_url + "/measurement/measurements"
    headers = c8y_http.HEADER_MEASUREMENT_JSON

    data = {
        register.name : {
            "T": {
                "value": value,
                "unit": "C"
            }
        },

        "time": datetime.datetime.utcnow().isoformat(),
        "source": {"id": slave.c8y_id},
        "type": register.c8y_type
    }
    resp = requests.post(request_url, auth=agent.auth, data=json.dumps(data), headers=headers)
    if resp.status_code == 201:
        print "[i] Sent measurement: ", resp.text
    else:
        print "[e] Could not send measurement: ", resp.text


if __name__ == '__main__':
    agent = Agent(MODBUS_TEMPLATE, CUMU_URL, TENANT_ID)
    agent.name = "ModbusPal Agent"
    agent.serial_no = "modbuspal"

    agent.modbus_client.open_connection()

    for slave in agent.slaves:
        for register in slave.registers:
            count = register.count

            result = agent.modbus_client.read_holdingregister_float32(slave.address, register.address)
            send_register_measurement(result, slave, register)

    agent.modbus_client.close_connection()