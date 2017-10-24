import json

from c8y import C8yDevice
from modbus.ModbusClient import ModbusClient, Slave

DEVICE_JSON = "./device.json"
CREDENTIALS_FILE = "./credentials.json"
CUMU_URL = "https://testing.iot.cs.ut.ee/"
TENANT_ID = "testing"

''' Translates MODBUS slave devices to Cumulocity Inventory'''
class Agent(C8yDevice):
    def __init__(self, templatefile, url, tenant):
        C8yDevice.__init__(self, url, tenant)

        self.name = "MODBUS Agent"
        self.slaves = []
        self.modbus_conf = {}
        self.modbus_client = ModbusClient('localhost', 502)


        self.bootstrap()
        self.discover_modbus_network(templatefile)
        self.bootstrap_c8y_children()

    def discover_modbus_network(self, templatefile):
        # Load file
        with open(templatefile) as template:
            self.modbus_conf = json.load(template)

        # Verify template file
        # TODO!

        # Iterate slaves, create devices
        for slave in self.modbus_conf["slaves"]:
            self.slaves.append(Slave(slave))

    def bootstrap_c8y_children(self):
        for slave in self.slaves:
            child_id = self.child_exists_with_name(slave.id)

            if child_id is None:
                # Create child device in inventory
                supported_measurements = set()
                for r in slave.registers:
                    supported_measurements.add(r.c8y_type)
                child_id = self.spawn_child_device(slave.id, list(supported_measurements))
            slave.c8y_id = child_id
            self.child_ids.append(child_id) # TODO: Improve storing/managing/refreshing references of children





