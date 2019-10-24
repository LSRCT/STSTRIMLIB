"""
Class to recieve LSL data containing for example sensor tag data
-AN
"""
import matplotlib.pyplot as plt
import pylsl


class BSDLSL_collector:
    def __init__(self, names):
        self.inlet_names = names
        self.inlet_list = []
        self.accX = 0
        self.accY = 0
        self.accZ = 0
        self.plotrange = 100
        self.plt_time = []
        self.plt_data = []

    def setup_inlets(self):
        """
        Search for all the inlets with names in self.inlet_names
        """
        for iname in self.inlet_names:
            streams = pylsl.resolve_stream('name', iname)
            self.inlet_list.append(pylsl.StreamInlet(streams[0]))

    def collect_data(self):
        """
        Continuously gathers data from set up inlets.
        """
        data = dict()
        for inlet, iname in zip(self.inlet_list, self.inlet_names):
            sample, timestamp = inlet.pull_sample()
            self.plt_time.append(timestamp)
            self.plt_data.append(sample)
            data[iname] = timestamp, sample
        return data

    def setup_plot(self):
        """
        Set up a plot for acceleration data
        """
        self.fig, self.ax = plt.subplots(1, 1)
        plt.ion()
        self.accX, = self.ax.plot([], [], label="X-Acceleration")
        self.accY, = self.ax.plot([], [], label="Y-Acceleration")
        self.accZ, = self.ax.plot([], [], label="Z-Acceleration")
        self.ax.legend(loc="upper left")


    def update_plot(self):
        """
        Update the acceleration plot
        :return: does it?
        """
        if len(self.plt_time) > self.plotrange:
            self.plt_time = self.plt_time[-self.plotrange:]
            self.plt_data = self.plt_data[-self.plotrange:]
        self.accX.set_ydata([x[2] for x in self.plt_data])
        self.accX.set_xdata(self.plt_time)
        self.accY.set_ydata([x[1] for x in self.plt_data])
        self.accY.set_xdata(self.plt_time)
        self.accZ.set_ydata([x[0] for x in self.plt_data])
        self.accZ.set_xdata(self.plt_time)
        plt.pause(1e-17)
        self.ax.relim()
        self.ax.autoscale_view()
        plt.draw()


if __name__ == "__main__":
    collector = BSDLSL_collector(["MovementSensor"])
    collector.setup_inlets()
    collector.setup_plot()
    while 1:
        collector.collect_data()
        collector.update_plot()
