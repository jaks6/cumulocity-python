import datetime
import json
import struct

import requests

from c8y import c8y_http
from modbus.Agent import Agent

CUMU_URL = "https://testing.iot.cs.ut.ee/"
TENANT_ID = "testing"

MODBUS_TEMPLATE = "./modbus.json"

agent = Agent(MODBUS_TEMPLATE, CUMU_URL, TENANT_ID)
agent.name = "ModbusPal Agent"
agent.serial_no = "modbuspal"


agent.modbus_client.connect()


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


def parse_ieee32bitfloat(result):
    msw = result.registers[0]
    lsw = result.registers[1]
    # 32-bit IEEE floating point number as used by ModbusPal:
    # 1 bit sign + 8 bits exponent + 23 bits fraction
    float32 = (msw << 16) + lsw
    # simple way of getting the value in human readable form:
    return struct.unpack('f', struct.pack('I', float32))[0]


for slave in agent.slaves:
    for register in slave.registers:

        address = register.address
        count = register.count

        result = agent.modbus_client.read_holding_registers(address=address-1, count=count, unit=slave.address)
        assert (result.function_code < 0x80)  # test that we are not an error

        value = parse_ieee32bitfloat(result)
        send_register_measurement(value, slave, register)

