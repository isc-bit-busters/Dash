from dash import callback, Output, Input, State, ctx, html
from utils.log_utils import add_log, add_mqtt_log
from utils.race_utils import race_state
from agents.sender_agent import send_message_to_robot
from mqtt.mqtt_client import send_mqtt_command
from utils.mac_utils import save_mac_addresses
from utils.connection_status import get_all_gate_statuses

from config import ROBOT_NAMES, TOP_CAMERA_NAME, PENALTY_TIME_SECONDS
import dash
import json

def register_callbacks(app):
    @callback(
        *[Output(f"{robot_id}-logs", "children") for robot_id in ROBOT_NAMES],
        *[Output(f"{robot_id}-image", "src") for robot_id in ROBOT_NAMES],
        *[Output(f"{robot_id}-penalty-count", "children") for robot_id in ROBOT_NAMES],
        Output(f"{TOP_CAMERA_NAME}-image", "src"),
        Output('mqtt-log-display', 'children'),
        Output("live-timer", "children"),
        Output("delta-timer", "children"),
        Input('update-interval', 'n_intervals'),
        State('live-timer', 'children'),
    )
    def update_ui(n, current_timer):
        from utils.log_utils import robot_logs, mqtt_logs, latest_frames
        from datetime import datetime

        now = datetime.now()
        if race_state["running"] and race_state["start_time"]:
            # race_state["elapsed"] = (now - race_state["start_time"]).total_seconds()
            base_elapsed = (now - race_state["start_time"]).total_seconds()
            penalty_time = sum(race_state.get("penalties", {}).values()) * PENALTY_TIME_SECONDS
            race_state["elapsed"] = base_elapsed + penalty_time

        finish_times = list(race_state["finish_times"].values())
        if race_state["running"] and len(finish_times) == 1:
            delta = abs((now - finish_times[0]).total_seconds())
            delta_display = f"{delta:.3f} s"
        else:
            delta_display = f"{race_state['delta']:.3f} s" if race_state['delta'] is not None else "N/A"

        timer_display = f"{race_state['elapsed']:.3f} s"

        robot_logs_html = [
            [html.Li(log) for log in list(robot_logs[robot_id])]
            for robot_id in ROBOT_NAMES
        ]

        robot_images_src = [
            f"data:image/jpeg;base64,{latest_frames[robot_id]}" if latest_frames[robot_id] else ""
            for robot_id in ROBOT_NAMES
        ]

        robot_penalty_counts = [
            html.Div(f"Penalties: {race_state['penalties'][robot_id]}", style={"color": "red", "fontWeight": "bold"}) if race_state['penalties'][robot_id] > 0 else ""
            for robot_id in ROBOT_NAMES
        ]

        top_camera_img = f"data:image/jpeg;base64,{latest_frames[TOP_CAMERA_NAME]}" if latest_frames[TOP_CAMERA_NAME] else ""

        mqtt_display_logs = [html.Li(log) for log in list(mqtt_logs)]

        return *robot_logs_html, *robot_images_src, *robot_penalty_counts, top_camera_img, mqtt_display_logs, timer_display, delta_display

    @app.callback(
        Output("reset-status", "children"),
        Output("reset-race-clear-interval", "n_intervals"),
        Input("reset-race", "n_clicks"),
        Input("reset-race-clear-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def reset_race(n_clicks, interval_triggered):
        triggered = ctx.triggered_id
        if triggered == "reset-race":
            race_state["start_time"] = None
            race_state["finish_times"] = {}
            race_state["running"] = False
            race_state["elapsed"] = 0.0
            race_state["delta"] = None
            race_state["penalties"] = {robot: 0 for robot in ROBOT_NAMES}
            add_mqtt_log("[RACE 🔄] Race has been reset via dashboard")
            return "Race has been reset.", 0
        elif triggered == "reset-race-clear-interval":
            return "", dash.no_update
        return dash.no_update, dash.no_update


    @app.callback(
        Output("robots-start", "disabled"),
        Output("robots-stop", "disabled"),
        Input("robots-start", "n_clicks"),
        Input("robots-stop", "n_clicks"),
        State("robots-start", "disabled"),
        prevent_initial_call=True
    )
    def toggle_robot(start_clicks, stop_clicks, is_start_disabled):
        triggered_id = ctx.triggered_id
        from utils.log_utils import robot_states
        if triggered_id and triggered_id.endswith('start'):
            print("Start button clicked", flush=True)
            for robot_id in ROBOT_NAMES:
                robot_states[robot_id] = True
                send_message_to_robot(robot_id, "start", "dashboardClient")
            return True, False
        elif triggered_id and triggered_id.endswith('stop'):
            print("Stop button clicked", flush=True)
            for robot_id in ROBOT_NAMES:
                robot_states[robot_id] = False
                send_message_to_robot(robot_id, "stop", "dashboardClient")
            return False, True
        return dash.no_update, dash.no_update

    # For each robot, create a callback for the penalty button
    for robot_id in ROBOT_NAMES:
        @app.callback(
            Output(f"{robot_id}-penalty", "disabled"),
            Output(f"{robot_id}-penalty-status", "children"),
            Output(f"{robot_id}-penalty-cooldown", "n_intervals"),
            Input(f"{robot_id}-penalty", "n_clicks"),
            Input(f"{robot_id}-calibrate", "n_clicks"),
            Input(f"{robot_id}-penalty-cooldown", "n_intervals"),
            prevent_initial_call=True
        )
        def handle_penalty(penalty_clicks, validate_clicks, cooldown_interval, _robot_id=robot_id):
            triggered = ctx.triggered_id
            if triggered == f"{_robot_id}-penalty":
                # send_message_to_robot(_robot_id, "penalty", "dashboardClient")
                # print(f"Penalty sent to {_robot_id}", flush=True)

                if not race_state["running"]:
                    log_msg = "⛔ Cannot apply penalty: Race not running."
                    add_log(_robot_id, log_msg)
                    return True, log_msg, 0
                race_state["penalties"][_robot_id] += 1
                race_state["elapsed"] += PENALTY_TIME_SECONDS
                log_msg = f"[PENALTY] +{PENALTY_TIME_SECONDS}s penalty applied to {_robot_id}. Total penalties: {race_state['penalties'][_robot_id]}"
                add_log(_robot_id, log_msg)
                return True, log_msg, 0
            elif triggered == f"{_robot_id}-penalty-cooldown":
                return False, "", dash.no_update
            elif triggered == f"{_robot_id}-calibrate":
                send_message_to_robot(_robot_id, "calibrate", "dashboardClient")
                print(f"Calibration sent to {_robot_id}", flush=True)
                return dash.no_update, "Calibration sent!", dash.no_update

            return dash.no_update, dash.no_update, dash.no_update

    @callback(
        Output("capture-status", "children"),
        Output("capture-status-clear-interval", "n_intervals"),
        Input("capture-top-image-btn", "n_clicks"),
        Input("validate-top-image-btn", "n_clicks"),
        Input("capture-status-clear-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def capture_new_top_image(cap_clicks, val_clicks, interval_triggered):
        triggered = ctx.triggered_id
        if triggered == "capture-top-image-btn":
            print("Capture request sent to top camera", flush=True)
            for robot_id in ROBOT_NAMES:
                send_message_to_robot(robot_id, "take_picture", "dashboardClient")
            # send_message_to_robot(TOP_CAMERA_NAME, "take_picture", "dashboardClient")
            return "📸 Capture request sent!", 0
        elif triggered == "capture-status-clear-interval":
            return "", dash.no_update
        elif triggered == "validate-top-image-btn":
            print("Validation request sent to top camera", flush=True)
            for robot_id in ROBOT_NAMES:
                send_message_to_robot(robot_id, "validate", "dashboardClient")
            # send_message_to_robot(TOP_CAMERA_NAME, "validate", "dashboardClient")
            return "✅ Validation request sent!", 0
        return dash.no_update, dash.no_update
    
    @app.callback(
        Output("gate1-start-status", "children"),
        Output("gate1-finish-status", "children"),
        Output("gate2-start-status", "children"),
        Output("gate2-finish-status", "children"),
        Input("update-interval", "n_intervals")
    )
    def update_gate_connection_status(n):
        statuses = get_all_gate_statuses()

        def dot(connected):
            return "🟢" if connected else "🔴"

        return (
            dot(statuses["gate1/start"]),
            dot(statuses["gate1/finish"]),
            dot(statuses["gate2/start"]),
            dot(statuses["gate2/finish"]),
        )

    @app.callback(
        Output("gate-mac-status", "children"),
        Output("gate-mac-clear-interval", "n_intervals"),
        Input("send-gate-macs", "n_clicks"),
        Input("gate-mac-clear-interval", "n_intervals"),
        State("gate1-start-mac", "value"),
        State("gate1-finish-mac", "value"),
        State("gate2-start-mac", "value"),
        State("gate2-finish-mac", "value"),
        prevent_initial_call=True,
    )
    def send_gate_mac_addresses(gate_clicks, gate_clear, gate1_start, gate1_finish, gate2_start, gate2_finish):
        triggered = ctx.triggered_id

        gate_status = dash.no_update
        gate_clear_trigger = dash.no_update

        if triggered == "send-gate-macs":
            if gate1_start and gate1_finish and gate2_start and gate2_finish:
                save_mac_addresses({
                    "gate1_start": gate1_start,
                    "gate1_finish": gate1_finish,
                    "gate2_start": gate2_start,
                    "gate2_finish": gate2_finish
                })
                payload = [
                    {"name": "s1", "address": gate1_start, "topic": "gate1/start"},
                    {"name": "e1", "address": gate1_finish, "topic": "gate1/finish"},
                    {"name": "s2", "address": gate2_start, "topic": "gate2/start"},
                    {"name": "e2", "address": gate2_finish, "topic": "gate2/finish"}
                ]

                payload_json = json.dumps(payload)  # Correct serialization
                send_mqtt_command("gate/mac_config", payload_json)
                gate_status = f"✅ Gate MAC addresses sent: {payload}"
                gate_clear_trigger = 0
            else:
                gate_status = "⚠️ Please fill both Start and Finish MAC for Gate 1."
                gate_clear_trigger = 0

        elif triggered == "gate-mac-clear-interval":
            gate_status = ""

        return gate_status, gate_clear_trigger
    
    @app.callback(
        Output("mqtt-status", "children"),
        Output("xmpp-status", "children"),
        Output("connection-status-card", "style"),
        Input('update-interval', 'n_intervals')
    )
    def update_connection_status(n):
        import utils.connection_status as conn_status

        mqtt_connected = conn_status.is_mqtt_connected()
        xmpp_connected = conn_status.is_xmpp_connected()
        # print(f"MQTT Connected: {mqtt_connected}, XMPP Connected: {xmpp_connected}", flush=True)
        mqtt_text = "" if mqtt_connected else "❌ MQTT Not Connected"
        xmpp_text = "" if xmpp_connected else "❌ XMPP Not Connected"
        
        # if both are connected, hide card
        if mqtt_connected and xmpp_connected:
            card_style = {"display": "none"}
        else:
            card_style = {"display": "block"}
        
        return mqtt_text, xmpp_text, card_style