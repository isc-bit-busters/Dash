from utils.log_utils import parse_timestamp, add_mqtt_log

race_state = {
    "start_time": None,
    "finish_times": {},
    "running": False,
    "elapsed": 0.0,
    "delta": None
}

def handle_gate_event(topic, payload):
    global race_state

    timestamp = parse_timestamp(payload)

    print(f"{timestamp} received from payload {payload}", flush=True)

    if "start" in topic and payload == "object_detected":
        if not race_state["running"]:
            race_state["start_time"] = timestamp
            race_state["running"] = True
            race_state["delta"] = None
            add_mqtt_log(f"[RACE] Start triggered at {timestamp.time()}")
        else:
            add_mqtt_log(f"[RACE] Start gate already triggered")

    elif "finish" in topic and payload == "object_detected":
        if topic not in race_state["finish_times"] and race_state["running"]:
            race_state["finish_times"][topic] = timestamp
            add_mqtt_log(f"[RACE] Finish {topic} at {timestamp.time()}")

            if len(race_state["finish_times"]) >= 2:
                finish_times = list(race_state["finish_times"].values())
                first_finish = min(finish_times)
                last_finish = max(finish_times)
                race_state["delta"] = abs((finish_times[0] - finish_times[1]).total_seconds())
                race_state["elapsed"] = (last_finish - race_state["start_time"]).total_seconds()
                race_state["running"] = False

                add_mqtt_log(f"[RACE ✅] Total time: {race_state['elapsed']:.3f}s | Δ Finish: {race_state['delta']:.3f}s")
        else:
            add_mqtt_log(f"[RACE] Finish gate {topic} already triggered")