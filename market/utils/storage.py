import pickle, os, glob, shutil

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

def timestamp(name):
    fileName = name+'.pickle'
    if not os.path.exists(fileName):
        return None
    return os.path.getmtime(fileName)

def backup(name):
    basename = os.path.basename(name)
    dirname = os.path.dirname(name)
    filename ='%s.pickle' % name
    backup_dir =  '%s/backup' % dirname
    filename_backup ='%s/%s_01.pickle' % (backup_dir, basename)
    filenames_backup_wildcard ='%s/%s_*.pickle' % (backup_dir, basename)

    # create backup dir if it does not exist
    if not os.path.exists(backup_dir): os.mkdir(backup_dir)
    
    backup_files = glob.glob(filenames_backup_wildcard)
    backup_files = [os.path.normpath(filename).replace('\\', '/') for filename in backup_files]
    backup_files.sort(reverse=True)
    
    # move files up a version
    if filename_backup in backup_files:
        # move files up
        for filename_old in backup_files:
            splits = filename_old.split(basename)
            old_version = int(splits[1].strip('_').strip('.pickle'))
            if old_version > 4:
                os.remove(filename_old)
                continue
            new_version = old_version + 1
            new_version = "{:02d}".format(new_version)
            filename_new = '%s/%s_%s.pickle' % (backup_dir,basename,new_version)
            shutil.move(filename_old, filename_new)

    try:
        shutil.copyfile(filename, filename_backup)
    except FileNotFoundError:
        pass
