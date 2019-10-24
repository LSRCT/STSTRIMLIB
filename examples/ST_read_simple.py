"""
Simple example to read the SensorTag temperature.
-AN
"""
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from pyLinkAPI import SensorTag


def read_simple(st):
    print("ModelNr: ", st.getData("ModelNr"))
    print("Battery: ", st.getData("Battery"))
    while 1:
        print("Temperature %f °C" % st.getData("Temperature"))


if __name__ == "__main__":
    tag = SensorTag("CC:78:AB:7F:75:03")
    tag.init_bt()
    read_simple(tag)

