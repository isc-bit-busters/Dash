from utils.log_utils import parse_timestamp, add_mqtt_log

from config import ROBOT_NAMES, PENALTY_TIME_SECONDS

race_state = {
    "start_time": None,
    "finish_times": {},
    "running": False,
    "elapsed": 0.0,
    "delta": None,
    "penalties": {robot: 0 for robot in ROBOT_NAMES},
}

def handle_gate_event(topic, payload):
    global race_state

    timestamp = parse_timestamp(payload)

    print(f"{timestamp} received from payload {payload}", flush=True)

    if "start" in topic and payload == "object_detected":
        if not race_state["running"] and race_state["start_time"] is None:
            race_state["start_time"] = timestamp
            race_state["running"] = True
            race_state["delta"] = None
            add_mqtt_log(f"[RACE] Start triggered at {timestamp.time()}")
        elif race_state["running"]:
            add_mqtt_log("[RACE] Start gate already triggered")
        else:
            add_mqtt_log("[RACE] Already started, need to reset to restart")


    elif "finish" in topic and payload == "object_detected":
        if topic not in race_state["finish_times"] and race_state["running"]:
            race_state["finish_times"][topic] = timestamp
            add_mqtt_log(f"[RACE] Finish {topic} at {timestamp.time()}")

            if len(race_state["finish_times"]) >= 2:
                finish_times = list(race_state["finish_times"].values())
                first_finish = min(finish_times)
                last_finish = max(finish_times)
                race_state["delta"] = abs((finish_times[0] - finish_times[1]).total_seconds())
                base_elapsed = (last_finish - race_state["start_time"]).total_seconds()
                penalty_time = sum(race_state.get("penalties", {}).values()) * PENALTY_TIME_SECONDS
                race_state["elapsed"] = base_elapsed + penalty_time
                race_state["running"] = False

                add_mqtt_log(
                    f"[RACE ✅] Base: {base_elapsed:.3f}s + Penalty: {penalty_time:.3f}s = Total: {race_state['elapsed']:.3f}s | Δ Finish: {race_state['delta']:.3f}s"
                )
        else:
            add_mqtt_log(f"[RACE] Finish gate {topic} already triggered")