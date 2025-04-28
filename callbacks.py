from dash import callback, Output, Input, State, ctx, html
from utils.log_utils import add_log, add_mqtt_log
from utils.race_utils import race_state
from agents.sender_agent import send_message_to_robot
from mqtt.mqtt_client import send_mqtt_command
from utils.mac_utils import save_mac_addresses

import dash



def register_callbacks(app):
    @callback(
        Output('robot1-logs', 'children'),
        Output('robot2-logs', 'children'),
        Output('robot1-image', 'src'),
        Output('robot2-image', 'src'),
        Output("top-camera-image", "src"),
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
            race_state["elapsed"] = (now - race_state["start_time"]).total_seconds()

        finish_times = list(race_state["finish_times"].values())
        if race_state["running"] and len(finish_times) == 1:
            delta = abs((now - finish_times[0]).total_seconds())
            delta_display = f"{delta:.3f} s"
        else:
            delta_display = f"{race_state['delta']:.3f} s" if race_state['delta'] is not None else "N/A"

        timer_display = f"{race_state['elapsed']:.3f} s"

        r1_logs = [html.Li(log) for log in list(robot_logs['robot1'])]
        r2_logs = [html.Li(log) for log in list(robot_logs['robot2'])]
        mqtt_display_logs = [html.Li(log) for log in list(mqtt_logs)]

        r1_img = f"data:image/jpeg;base64,{latest_frames['robot1']}" if latest_frames['robot1'] else ""
        r2_img = f"data:image/jpeg;base64,{latest_frames['robot2']}" if latest_frames['robot2'] else ""
        top_camera_img = f"data:image/jpeg;base64,{latest_frames['top_camera']}" if latest_frames['top_camera'] else ""

        return r1_logs, r2_logs, r1_img, r2_img, top_camera_img, mqtt_display_logs, timer_display, delta_display

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
            add_mqtt_log("[RACE 🔄] Race has been reset via dashboard")
            return "Race has been reset.", 0
        elif triggered == "reset-race-clear-interval":
            return "", dash.no_update
        return dash.no_update, dash.no_update


    for robot_id in ['robot1', 'robot2']:
        @app.callback(
            Output(f"{robot_id}-start", "disabled"),
            Output(f"{robot_id}-stop", "disabled"),
            Input(f"{robot_id}-start", "n_clicks"),
            Input(f"{robot_id}-stop", "n_clicks"),
            State(f"{robot_id}-start", "disabled"),
            prevent_initial_call=True
        )
        def toggle_robot(start_clicks, stop_clicks, is_start_disabled, _robot_id=robot_id):
            triggered_id = ctx.triggered_id
            from utils.log_utils import robot_states
            if triggered_id and triggered_id.endswith('start'):
                robot_states[_robot_id] = True
                send_message_to_robot(_robot_id, "start", "dashboardClient")
                return True, False
            elif triggered_id and triggered_id.endswith('stop'):
                robot_states[_robot_id] = False
                send_message_to_robot(_robot_id, "stop", "dashboardClient")
                return False, True
            return dash.no_update, dash.no_update

    for robot_id in ['robot1', 'robot2']:
        @app.callback(
            Output(f"{robot_id}-penalty", "disabled"),
            Output(f"{robot_id}-penalty-status", "children"),
            Output(f"{robot_id}-penalty-cooldown", "n_intervals"),
            Input(f"{robot_id}-penalty", "n_clicks"),
            Input(f"{robot_id}-penalty-cooldown", "n_intervals"),
            prevent_initial_call=True
        )
        def handle_penalty(penalty_clicks, cooldown_interval, _robot_id=robot_id):
            triggered = ctx.triggered_id
            if triggered == f"{_robot_id}-penalty":
                send_message_to_robot(_robot_id, "penalty", "dashboardClient")
                return True, "Penalty sent!", 0
            elif triggered == f"{_robot_id}-penalty-cooldown":
                return False, "", dash.no_update
            return dash.no_update, dash.no_update, dash.no_update

    @callback(
        Output("capture-status", "children"),
        Output("capture-status-clear-interval", "n_intervals"),
        Input("capture-top-image-btn", "n_clicks"),
        Input("capture-status-clear-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def capture_new_top_image(n_clicks, interval_triggered):
        triggered = ctx.triggered_id
        if triggered == "capture-top-image-btn":
            send_message_to_robot("top_camera", "take_picture", "dashboardClient")
            return "📸 Capture request sent!", 0
        elif triggered == "capture-status-clear-interval":
            return "", dash.no_update
        return dash.no_update, dash.no_update

    @app.callback(
        Output("mqtt-command-status", "children"),
        Output("mqtt-command-clear-interval", "n_intervals"),
        Input("send-mqtt-btn", "n_clicks"),
        Input("mqtt-command-clear-interval", "n_intervals"),
        prevent_initial_call=True
    )
    def send_mqtt_command_callback(n_clicks, n_intervals):
        triggered = ctx.triggered_id
        if triggered == "send-mqtt-btn":
            topic = "gate/ir"
            command = "reset"
            send_mqtt_command(topic, command)
            return f"Command '{command}' sent to topic '{topic}'", 0
        elif triggered == "mqtt-command-clear-interval":
            return "", dash.no_update
        return dash.no_update, dash.no_update



    @app.callback(
        Output("gate1-mac-status", "children"),
        Output("gate2-mac-status", "children"),
        Output("gate1-mac-clear-interval", "n_intervals"),
        Output("gate2-mac-clear-interval", "n_intervals"),
        Input("send-gate1-macs", "n_clicks"),
        Input("send-gate2-macs", "n_clicks"),
        Input("gate1-mac-clear-interval", "n_intervals"),
        Input("gate2-mac-clear-interval", "n_intervals"),
        State("gate1-start-mac", "value"),
        State("gate1-finish-mac", "value"),
        State("gate2-start-mac", "value"),
        State("gate2-finish-mac", "value"),
        prevent_initial_call=True,
    )
    def send_gate_mac_addresses(gate1_clicks, gate2_clicks, gate1_clear, gate2_clear, gate1_start, gate1_finish, gate2_start, gate2_finish):
        triggered = ctx.triggered_id

        gate1_status = dash.no_update
        gate2_status = dash.no_update
        gate1_clear_trigger = dash.no_update
        gate2_clear_trigger = dash.no_update

        if triggered == "send-gate1-macs":
            if gate1_start and gate1_finish:
                save_mac_addresses({
                    "gate1_start": gate1_start,
                    "gate1_finish": gate1_finish,
                    "gate2_start": gate2_start,
                    "gate2_finish": gate2_finish
                })
                payload = {"start_mac": gate1_start, "finish_mac": gate1_finish}
                send_mqtt_command("gate1/mac_config", str(payload))
                gate1_status = f"✅ Gate 1 MAC addresses sent: {payload}"
                gate1_clear_trigger = 0
            else:
                gate1_status = "⚠️ Please fill both Start and Finish MAC for Gate 1."
                gate1_clear_trigger = 0

        if triggered == "send-gate2-macs":
            if gate2_start and gate2_finish:
                save_mac_addresses({
                    "gate1_start": gate1_start,
                    "gate1_finish": gate1_finish,
                    "gate2_start": gate2_start,
                    "gate2_finish": gate2_finish
                })

                payload = {"start_mac": gate2_start, "finish_mac": gate2_finish}
                send_mqtt_command("gate2/mac_config", str(payload))
                gate2_status = f"✅ Gate 2 MAC addresses sent: {payload}"
                gate2_clear_trigger = 0
            else:
                gate2_status = "⚠️ Please fill both Start and Finish MAC for Gate 2."
                gate2_clear_trigger = 0

        elif triggered == "gate1-mac-clear-interval":
            gate1_status = ""
        elif triggered == "gate2-mac-clear-interval":
            gate2_status = ""

        return gate1_status, gate2_status, gate1_clear_trigger, gate2_clear_trigger
    
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