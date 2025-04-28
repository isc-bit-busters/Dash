# Variables
_xmpp_connected = False
_mqtt_connected = False

# Getter functions
def is_xmpp_connected():
    return _xmpp_connected

def is_mqtt_connected():
    return _mqtt_connected

# Setter functions
def set_xmpp_connected(status: bool):
    global _xmpp_connected
    print(f"XMPP connection status set to: {status}", flush=True)
    _xmpp_connected = status

def set_mqtt_connected(status: bool):
    global _mqtt_connected
    print(f"MQTT connection status set to: {status}", flush=True)
    _mqtt_connected = status
