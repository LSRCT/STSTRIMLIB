"""
Simple example to recieve an LSL inlet with SensorTag data and plot it.
"""
import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from BSDLSL import BSDLSL_collector


def receive_simple(col):
    col.setup_inlets()
    col.setup_plot()
    while 1:
        print(col.collect_data())
        col.update_plot()


if __name__ == "__main__":
    collector = BSDLSL_collector(["MovementSensor"])
    receive_simple(collector)
