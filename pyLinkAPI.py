# -*- coding: utf-8 -*-
"""
TI CC2650 SensorTag communicator class.
-------------------
Class for reading the sensor data and transmit it via LSL in a simple way.
-AN
TODO async stuff can be handled by a wrapper
"""
import struct
import pylsl
import sys

from bleak import BleakClient
from bleak.exc import BleakError


class SensorTag:
    def __init__(self, address):
        """
        Sensor tag class init
        :param address: Mac address of the sensor tag
        """
        self.__name__ = "SensorTag1"
        self.address = address
        self.bClient = BleakClient(address)
        self.UUIDS = dict()
        self.ch_counts = dict()
        self.evals = dict()
        self.init_info_dicts()
        self.init_eval_dict()
        self.scale = 8.0 / 32768.0
        self.verbose = 1
        self.stream_infos = []
        self.stream_outlets = []

    def error_wrapper(func):
        """
        Decorator for error wrapping to keep the error output simple. TODO needs expansion
        :return: the function return if no error occurs.
        """
        def wrapper(*args):
            try:
                ret = func(*args)
                return ret
            except BleakError as err:
                if "Device with address" in str(err):
                    print("Connection to " + str(err).split()[3]+" failed, is the device turned on and the mac address correct?")
                    sys.exit(1)
                if "Characteristic" in str(err):
                    print("Data send/recieve failed. Initiate the device correctly and check the UUIDs.")
                    sys.exit(2)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                raise
        return wrapper

    def _TI_UUID(self, val):
        """
        Simple method to format hex numbers correctly for UUIDs
        :param val: Hex val
        :return: Full UUID
        """
        return ("%08X-0451-4000-b000-000000000000" % (0xf0000000 + val)).lower()


    def init_info_dicts(self):
        """
        Inits a dict with UUIDs for reading the different sensors
        """
        self.UUIDS = {"Battery": "00002a19-0000-1000-8000-00805f9b34fb",
                      "ModelNr": "00002a24-0000-1000-8000-00805f9b34fb",
                      "Temperature": self._TI_UUID(0xaa01),
                      "MovementSensor": self._TI_UUID(0xaa81),
                      "HumiditySensor": self._TI_UUID(0xAA21),
                      "OpticalSensor": self._TI_UUID(0xAA71)}


    def init_eval_dict(self):
        """
        Inits a dict with functions to evaluate the recieved sensor data for different sensors
        """
        self.evals = {"Battery": lambda a: int(a[0]),
                      "ModelNr": lambda a: "".join(map(chr, a)),
                      "Temperature": self.calcTemp,
                      "MovementSensor": self.calcMov,
                      "HumiditySensor": self.calcHum,
                      "OpticalSensor": self.calcLight}

        self.ch_counts = {"Battery": 1,
                      "ModelNr": 1,
                      "Temperature": 1,
                      "MovementSensor": 3,
                      "HumiditySensor": 1,
                      "OpticalSensor": 1}


    @error_wrapper
    def init_bt(self, timeout=4):
        """
        inits the bluetooth connection and the sensors.
        :param timeout: Bluetooth search timeout
        """
        if self.verbose:
            print("Connecting to BLE device")
        self.bClient.loop.run_until_complete(self.connect_bt_async(timeout=timeout))
        self.bClient.loop.run_until_complete(self.init_sensors())
        if self.verbose:
            print("Connected")


    async def connect_bt_async(self, timeout):
        """
        asynchronus connect. Not to be called directly
        :param timeout:  Bluetooth search timeout
        """
        await self.bClient.connect(timeout=timeout)
        await self.bClient.is_connected()
        await self.bClient.get_services()

    async def init_sensors(self, ):
        """
        asynchronus init for sensors. Not to be called directly
        """
        if self.verbose:
            print("Initiation sensors")
        sensorOn = bytearray([0x01])
        await self.bClient.write_gatt_char(self._TI_UUID(0xaa02), sensorOn)  # activate temp sense
        await self.bClient.write_gatt_char(self._TI_UUID(0xaa22), sensorOn)  # activate humidity sense
        await self.bClient.write_gatt_char(self._TI_UUID(0xaa72), sensorOn)  # activate optical sense
        await self.bClient.write_gatt_char(self._TI_UUID(0xaa82), bytearray([int(b"00111000", 2), int(b"00000000", 2)]))  # activate movement sense
        await self.bClient.write_gatt_char(self._TI_UUID(0xaa83),  bytearray([0x0A]))  # activate movement sense
        if self.verbose:
            print("Sensors initiated")

    @error_wrapper
    def getData(self, name):
        """
        Gets data from the specified sensor. Name corresponds to a key in the UUID dict.
        :param name: name of the sensor
        """
        data = self.bClient.loop.run_until_complete(self.getData_async(self.UUIDS[name]))
        evalDat = self.evals[name](data)
        return evalDat

    async def getData_async(self, UUID):
        """
        asynchronus init for sensors. Not to be called directly
        :param UUID: UUID for the bluetooth read
        """
        data = await self.bClient.read_gatt_char(UUID)  # read temp
        return data

    def calcHum(self, hum0):
        """
        Eval function for humidity
        :param hum0: recieved data
        :return: humidity
        """
        (rawT, rawH) = struct.unpack('<HH', hum0)
        temp = -40.0 + 165.0 * (rawT / 65536.0)
        RH = 100.0 * (rawH / 65536.0)
        return RH

    def calcMov(self, mov0):
        """
        Eval function for movement TODO
        :param mov0: recieved data
        :return: movement data
        """
        (gyroZ, gyroY, gyroX) = struct.unpack('<hhh', mov0[:6])
        (accZ, accY, accX) = struct.unpack('<hhh', mov0[6:12])
        [accZ, accY, accX, gyroZ, gyroY, gyroX] = [(x*8) / 32768.0 for x in [accZ, accY, accX, gyroZ, gyroY, gyroX]]
        return [accZ, accY, accX, gyroZ, gyroY, gyroX]

    def calcTemp(self, temp0):
        """
        Eval function for temperature
        :param temp0: recieved data
        :return: temeprature in deg C
        """
        SCALE_LSB = 0.03125;
        (rawTobj, rawTamb) = struct.unpack('<hh', temp0)
        tObj = (rawTobj >> 2) * SCALE_LSB
        tAmb = (rawTamb >> 2) * SCALE_LSB
        #print("Temp: ", (tObj))
        #print("Temp: ", (tAmb))
        return tAmb

    def calcLight(self, light0):
        """
        Eval function for light sensor
        :param light0: recieved data
        :return: light sensor value
        """
        raw = struct.unpack('<h', light0)[0]
        m = raw & 0xFFF
        e = (raw & 0xF000) >> 12
        return 0.01 * (m << e)

    def start_continuous_stream(self, out_data_handles=[""]):
        """
        Designed to stream data to LSL. Should be used in its own threat
        :param out_data_handles: list of strings. Strings are the sensor names
        """
        for handle in out_data_handles:
            self.stream_infos.append(pylsl.StreamInfo(name=handle, type='tag',
                                               channel_count=self.ch_counts[handle], source_id=self.__name__))
            self.stream_outlets.append(pylsl.StreamOutlet(self.stream_infos[-1]))
            if self.verbose:
                print("Added %s to outlets" % handle)
        if self.verbose:
            print("Starting continuous outlets")
        while 1:
            for handle, stream_out in zip(out_data_handles, self.stream_outlets):
                out_data = self.getData(handle)[:3]
                stream_out.push_sample(out_data)


if __name__ == "__main__":
    tag = SensorTag("CC:78:AB:7F:75:03")
    tag.init_bt()
    print("ModelNr: ", tag.getData("ModelNr"))
    print("Battery: ", tag.getData("Battery"))
    tag.start_continuous_stream(out_data_handles=["MovementSensor"])
