# Variables
_xmpp_connected = False
_mqtt_connected = False

_gate_connection_status = {
    "gate1/start": False,
    "gate1/finish": False,
    "gate2/start": False,
    "gate2/finish": False,
}

# Getter functions
def is_xmpp_connected():
    return _xmpp_connected

def is_mqtt_connected():
    return _mqtt_connected

# Setter functions
def set_xmpp_connected(status: bool):
    global _xmpp_connected
    _xmpp_connected = status

def set_mqtt_connected(status: bool):
    global _mqtt_connected
    _mqtt_connected = status

def set_gate_status(topic, status: bool):
    if topic in _gate_connection_status:
        _gate_connection_status[topic] = status

def get_gate_status(topic):
    return _gate_connection_status.get(topic, False)

def get_all_gate_statuses():
    return _gate_connection_status.copy()