import struct
from pymodbus.client.sync import ModbusTcpClient

__author__ = 'Jakob'



class ModbusClient():
    ''' Connects to modbus slaves '''

    def __init__(self, server_addr='localhost', server_port=502):
        self.server_ip = server_addr
        self.server_port = server_port

        self.client = ModbusTcpClient(server_addr, port=server_port)

    def open_connection(self):
        self.client.connect()

    def close_connection(self):
        self.client.close()

    def read_single_coil(self):
        pass

    # Assumes 32-bit IEEE floating point number as used by ModbusPal:
    # 1 bit sign + 8 bits exponent + 23 bits fraction
    def read_holdingregister_float32(self, device_address, register_addr):
        translated_addr = register_addr - 1

        # read two consecutive registers
        result = self.client.read_holding_registers(address=translated_addr, count=2, unit=1)
        assert (result.function_code < 0x80)  # test that we are not an error

        msw = result.registers[0]
        lsw = result.registers[1]

        float32 = (msw << 16) + lsw
        value = struct.unpack('f', struct.pack('I', float32))[0]

        print "read float32 value:", value
        return value

class Slave():
    def __init__(self, json_conf):
        self.address = json_conf["address"]
        self.id = json_conf["id"]
        self.c8y_id = -1

        self.registers = []
        for r in json_conf["registers"]:
            self.registers.append(Register(r))

class Register():
    def __init__(self, json_conf):
        self.name = json_conf["name"]
        self.address = json_conf["address"]
        self.count = json_conf["count"]
        self.raw_type = json_conf["raw_type"]
        self.c8y_type = json_conf["c8y_type"]

