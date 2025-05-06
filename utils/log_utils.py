from collections import deque
from datetime import datetime

from config import ROBOT_NAMES, TOP_CAMERA_NAME

robot_logs = {robot: deque(maxlen=10) for robot in ROBOT_NAMES}

mqtt_logs = deque(maxlen=20)

arm_logs = deque(maxlen=3)

robot_states = {robot: False for robot in ROBOT_NAMES}

latest_frames = {robot: None for robot in ROBOT_NAMES}
latest_path_frames = {robot: None for robot in ROBOT_NAMES}
latest_frames[TOP_CAMERA_NAME] = None


def add_log(robot_id, message):
    if robot_id in robot_logs:
        robot_logs[robot_id].appendleft(message)

def add_mqtt_log(msg):
    mqtt_logs.appendleft(msg)

def add_arm_log(msg):
    arm_logs.appendleft(msg)

def parse_timestamp(ts_str):
    try:
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()