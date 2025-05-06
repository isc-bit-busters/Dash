import json
import os

from config import XMPP_MEMORY_FILE

def save_command_body_for_type(cmd_type, body):
    data = {}
    if os.path.exists(XMPP_MEMORY_FILE):
        with open(XMPP_MEMORY_FILE, "r") as f:
            data = json.load(f)
    data[cmd_type] = body
    with open(XMPP_MEMORY_FILE, "w") as f:
        json.dump(data, f)

def load_command_body_for_type(cmd_type):
    if os.path.exists(XMPP_MEMORY_FILE):
        with open(XMPP_MEMORY_FILE, "r") as f:
            data = json.load(f)
            return data.get(cmd_type, "")
    return ""
