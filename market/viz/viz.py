import matplotlib.pyplot as plt
from pprint import pp

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
    
    def data_text(self, data, file_name='data'):
        with open('%s.txt' % file_name, 'w', encoding='utf-8') as f:
            pp(data, f)
    
    @staticmethod
    def data_keys_text_recursive(data, data_keys, rename_set, rename_to):
        if isinstance(data, dict):
            for key, key_data in data.items():
                if isinstance(key, int):
                    key = 'int_key'
                elif len(rename_set) > 0 and key in rename_set:
                    key = rename_to
                if not key in data_keys:
                    data_keys[key] = {}
                Viz.data_keys_text_recursive(key_data, data_keys[key], rename_set, rename_to)
        elif isinstance(data, list):
            for key_data in data:
                Viz.data_keys_text_recursive(key_data, data_keys, rename_set, rename_to)
    
    def data_keys_text(self, data, file_name='data_keys', rename_set=set(), rename_to='idem'):
        data_keys = {}
        Viz.data_keys_text_recursive(data, data_keys, rename_set, rename_to)
        self.data_text(data_keys, file_name)


