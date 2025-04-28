import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPICS
from utils.log_utils import add_mqtt_log
from utils.race_utils import handle_gate_event
import utils.connection_status as conn_status

mqtt_pub_client = None  # publisher client

def create_mqtt_client(client_name="MQTT Client"):
    """Helper to create and connect a new MQTT client."""
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        conn_status.set_mqtt_connected(True)
        print(f"✅ {client_name} connected to MQTT broker.", flush=True)
        return client
    except Exception as e:
        conn_status.set_mqtt_connected(False)
        print(f"⚠️ Failed to connect {client_name}: {e}", flush=True)
        return None

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to MQTT broker with result code {rc}", flush=True)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic)
        print(f"📥 Subscribed to {topic}", flush=True)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    log_entry = f"[MQTT:{topic}] {payload}"
    add_mqtt_log(log_entry)
    print(log_entry, flush=True)

    if "start" in topic or "finish" in topic:
        handle_gate_event(topic, payload)

def start_mqtt_client():
    """Start the subscriber client (long running)."""
    client = create_mqtt_client("Subscriber Client")
    if client:
        client.on_connect = on_connect
        client.on_message = on_message
        client.loop_forever()

def init_mqtt_pub_client():
    """Initialize the publisher client (background loop)."""
    global mqtt_pub_client
    mqtt_pub_client = create_mqtt_client("Publisher Client")
    if mqtt_pub_client:
        mqtt_pub_client.loop_start()

def send_mqtt_command(topic, command):
    """Send a command using the persistent publisher client."""
    global mqtt_pub_client

    if mqtt_pub_client:
        try:
            mqtt_pub_client.publish(topic, command)
            print(f"✅ Published to {topic}: {command}", flush=True)
        except Exception as e:
            conn_status.set_mqtt_connected(False)
            mqtt_pub_client = None
            print(f"⚠️ Failed to publish MQTT command: {e}", flush=True)
    else:
        print(f"⚠️ MQTT publisher client not available to send '{command}' to '{topic}'", flush=True)
