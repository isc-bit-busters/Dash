import json
import os
from config import MAC_FILE

def save_mac_addresses(mac_data):
    with open(MAC_FILE, "w") as f:
        json.dump(mac_data, f)

def load_mac_addresses():
    if os.path.exists(MAC_FILE):
        with open(MAC_FILE, "r") as f:
            return json.load(f)
    return {"gate1_start": "", "gate1_finish": "", "gate2_start": "", "gate2_finish": ""}
