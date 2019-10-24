"""
Simple example to start an LSL outlet with SensorTag data.
"""
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from pyLinkAPI import SensorTag


def send_simple(st):
    st.start_continuous_stream(out_data_handles=["MovementSensor"])

if __name__ == "__main__":
    tag = SensorTag("CC:78:AB:7F:75:03")
    tag.init_bt()
    send_simple(tag)
