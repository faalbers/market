def stop_text():    
    with open('stop.txt', 'r') as f:
        if len(f.read()) > 0:
            return True
        return False
