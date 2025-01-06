import matplotlib.pyplot as plt

class Viz():
    def __init__(self):
        pass

    def plot_timeseries(self, data):
        fig, axs = plt.subplots(len(data), 1, figsize=(10, 10))
        axs_index = 0
        for name, df in data.items():
            axs[axs_index].plot(df)
            axs[axs_index].set_title(name)
            axs_index += 1
        plt.tight_layout()
        plt.show()