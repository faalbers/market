import pickle, os

def save(data, name):
    fileName = name+'.pickle'
    with open(fileName, 'wb') as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
    f.close()

def load(name):
    fileName = name+'.pickle'
    if not os.path.exists(fileName):
        return None
    with open(fileName, 'rb') as f:
        data = pickle.load(f)
    f.close()
    return data
