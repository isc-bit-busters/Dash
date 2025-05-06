import os

# Configuration for XMPP
XMPP_USERNAME = "receiverClient"
XMPP_SERVER = "prosody"
XMPP_PASSWORD = os.getenv("XMPP_PASSWORD", "plsnohack")

# Configuration for MQTT
MQTT_BROKER = "192.168.88.253"
MQTT_PORT = 1883
MQTT_TOPICS = [
    ("gate/ir", 0),
    ("gate1/start", 0),
    ("gate2/start", 0),
    ("gate1/finish", 0),
    ("gate2/finish", 0),
    ("gate/mac_config/ack", 0)
]

# Configuration save paths
MAC_FILE = "mac_addresses.json"
XMPP_MEMORY_FILE = "xmpp_command_memory.json"

# Configuration for robot names and camera
ROBOT_NAMES = ["gerald", "mael"]
TOP_CAMERA_NAME = "top_camera"

# Configuration for delay and penalty
PENALTY_TIME_SECONDS = 5