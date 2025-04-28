from collections import deque
from datetime import datetime


robot_logs = {
    'robot1': deque(maxlen=10),
    'robot2': deque(maxlen=10)
}

mqtt_logs = deque(maxlen=20)

robot_states = {
    'robot1': False,
    'robot2': False
}

latest_frames = {
    'robot1': None,
    'robot2': None,
    'top_camera' : None
}


def add_log(robot_id, message):
    if robot_id in robot_logs:
        robot_logs[robot_id].appendleft(message)

def add_mqtt_log(msg):
    mqtt_logs.appendleft(msg)

def parse_timestamp(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()