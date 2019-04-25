from random import random

import time

from modbus.Agent import Agent

CUMU_URL = "https://testing.iot.cs.ut.ee/"
TENANT_ID = "testing"

MODBUS_TEMPLATE = "./modbus.json"

agent = Agent(MODBUS_TEMPLATE, CUMU_URL, TENANT_ID)


for i in range(25):
    val = random() * 10 + 15
    print("Measurement ", val)
    # sends a measurement using the 1st child device id as the source
    agent.child_send_measurement(val) # method exists just for demo purposes
    time.sleep(2)
