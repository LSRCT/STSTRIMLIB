# STSTRIMLIB
Scripts for easily reading and sending TI Sensor Tag CC2650 sensor data.


Implements a SensorTag class to easily read the data. The class includes a function to use a pyLSL outlet to stream the data.
Includes a second class BSDLSL to recieve a pyLSL stream with SensorTag data.
Bluetooth communication is done via Bleak.

Requirements:
- pylsl
- bleak
- matplotlib (for plotting in BSDLSL)
- BLE module in the PC and a TI SensorTag (duh)
