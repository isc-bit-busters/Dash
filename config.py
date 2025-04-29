MQTT_BROKER = "192.168.88.253"
MQTT_PORT = 1883
MQTT_TOPICS = [
    ("gate/ir", 0),
    ("gate1/ir", 0),
    ("gate2/ir", 0),
    ("gate1/start", 0),
    ("gate2/start", 0),
    ("gate1/finish", 0),
    ("gate2/finish", 0)
]

MAC_FILE = "mac_addresses.json"

ROBOT_NAMES = ["gerald", "mael"]
TOP_CAMERA_NAME = "top_camera"