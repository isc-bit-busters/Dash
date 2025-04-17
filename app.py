import dash
from dash import html, dcc, callback, Output, Input, State, ctx
import dash_bootstrap_components as dbc
import time
import threading
from collections import deque
import numpy as np
from datetime import datetime

# For Spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
import asyncio
import os
import spade

# For MQTT
import paho.mqtt.client as mqtt

# ----------------------
# Globals
# ----------------------

MQTT_BROKER = "192.168.88.253"
MQTT_PORT = 1883
MQTT_TOPICS = [
    ("gate/ir", 0),
    ("gate1/ir", 0),
    ("gate2/ir", 0),

    ("gate/start1", 0),
    ("gate/start2", 0),
    ("gate/finish1", 0),
    ("gate/finish2", 0),
]

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
    'robot2': None
}

race_state = {
    "start_time": None,
    "finish_times": {},
    "running": False,
    "elapsed": 0.0,
    "delta": None
}

# -----------------
# Utility Functions
# -----------------

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
    


# ----------------------
# Dash Setup
# ----------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Multi-Robot Dashboard"

def robot_card(robot_id):
    return dbc.Card([
        dbc.CardHeader(html.H4(f"{robot_id.upper()}")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Img(id=f"{robot_id}-image", style={"width": "100%", "maxHeight": "240px"}), md=6),
                dbc.Col([
                    html.H5("Logs"),
                    html.Ul(id=f"{robot_id}-logs", className="log-list")
                ], md=6),
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col(dbc.Button("Start", id=f"{robot_id}-start", color="success", className="me-2")),
                dbc.Col(dbc.Button("Stop", id=f"{robot_id}-stop", color="danger")),
                dbc.Col([
                    dbc.Button("Penalty", id=f"{robot_id}-penalty", color="warning", n_clicks=0),
                    html.Div(id=f"{robot_id}-penalty-status", className="mt-2", style={"color": "green", "fontWeight": "bold"})
                ])
            ])
        ])
    ], className="mb-4")

app.layout = dbc.Container([
    html.H1("Robot Control Dashboard", className="my-4 text-center"),
    dbc.Row([
        dbc.Col(robot_card("robot1"), md=6),
        dbc.Col(robot_card("robot2"), md=6)
    ]),
    html.Hr(),
    html.H5("Race Timing Monitor", className="my-4 text-center"),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("⏱ Current Race Time"),
            dbc.CardBody(html.H4(id="live-timer", children="0.000 s", className="text-primary"))
        ]), md=6),
        dbc.Col(dbc.Card([
            dbc.CardHeader("Δ Time Between Finishes"),
            dbc.CardBody(html.H4(id="delta-timer", children="N/A", className="text-warning"))
        ]), md=6),
    ]),
    html.Div([
        dbc.Button("Reset Race", id="reset-race", color="danger", className="mt-3"),
        html.Div(id="reset-status", className="mt-2", style={"fontWeight": "bold", "color": "red"})
    ]),
    html.Hr(),
    dbc.Card([
        dbc.CardHeader("Latest Race Logs"),
        dbc.CardBody([
            html.Ul(id="mqtt-log-display", className="log-list", style={"maxHeight": "300px", "overflowY": "scroll"})
        ])
    ]),
    html.Div(id="mqtt-command-status"),  # Added missing component
    dbc.Button("Send MQTT Reset", id="send-mqtt-btn", color="secondary", className="mt-3"),
    dcc.Interval(id='update-interval', interval=10, n_intervals=0),
    dcc.Interval(id='robot1-penalty-cooldown', interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id='robot2-penalty-cooldown', interval=3000, n_intervals=0, max_intervals=1),
], fluid=True)


# ----------------------
# Callbacks
# ----------------------

# Update logs and images
@callback(
    Output('robot1-logs', 'children'),
    Output('robot2-logs', 'children'),
    Output('robot1-image', 'src'),
    Output('robot2-image', 'src'),
    Output('mqtt-log-display', 'children'),
    Output("live-timer", "children"),
    Output("delta-timer", "children"),
    Input('update-interval', 'n_intervals'),
    State('live-timer', 'children'),
)
def update_ui(n, current_timer):
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

    return r1_logs, r2_logs, r1_img, r2_img, mqtt_display_logs, timer_display, delta_display

@app.callback(
    Output("reset-status", "children"),
    Input("reset-race", "n_clicks"),
    prevent_initial_call=True
)
def reset_race(n_clicks):
    race_state["start_time"] = None
    race_state["finish_times"] = {}
    race_state["running"] = False
    race_state["elapsed"] = 0.0
    race_state["delta"] = None
    add_mqtt_log("[RACE 🔄] Race has been reset via dashboard")
    return "Race has been reset."

def send_message_to_robot(robot_id, message, sender_id="testClient"):
    def _send():
        async def run_sender():
            xmpp_server = "prosody"
            xmpp_password = os.getenv("XMPP_PASSWORD", "plsnohack")

            sender = SenderAgent(f"{sender_id}@{xmpp_server}", xmpp_password)
            await sender.start(auto_register=True)
            sender.add_behaviour(sender.SendBehaviour(robot_id, message))
            await asyncio.sleep(5)
            await sender.stop()
        
        asyncio.run(run_sender())
        print(f"[Sender] Message sent: '{message}' to {robot_id}", flush=True)

    threading.Thread(target=_send, daemon=True).start()

# Fix scoping with wrapper
def make_toggle_callback(robot_id):
    def toggle(start_clicks, stop_clicks, is_start_disabled):
        triggered_id = dash.ctx.triggered_id
        if triggered_id and triggered_id.endswith('start'):
            robot_states[robot_id] = True
            # Send message to robot
            send_message_to_robot(robot_id, "start", "dashboardClient")
            return True, False
        elif triggered_id and triggered_id.endswith('stop'):
            robot_states[robot_id] = False
            send_message_to_robot(robot_id, "stop", "dashboardClient")
            return False, True
        return dash.no_update, dash.no_update
    return toggle

# Register callback for each robot
for robot_id in ['robot1', 'robot2']:
    app.callback(
        Output(f"{robot_id}-start", "disabled"),
        Output(f"{robot_id}-stop", "disabled"),
        Input(f"{robot_id}-start", "n_clicks"),
        Input(f"{robot_id}-stop", "n_clicks"),
        State(f"{robot_id}-start", "disabled"),
        prevent_initial_call=True
    )(make_toggle_callback(robot_id))

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
            return True, "Penalty sent!", 0  # Disable button, show message, start cooldown
        elif triggered == f"{_robot_id}-penalty-cooldown":
            return False, "", dash.no_update  # Re-enable, clear message
        return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("mqtt-command-status", "children"),
    Input("send-mqtt-btn", "n_clicks"),
    prevent_initial_call=True
)
def send_mqtt_command_callback(n_clicks):
    topic = "gate/ir"
    command = "reset"
    send_mqtt_command(topic, command)
    return f"Command '{command}' sent to topic '{topic}'"

def handle_gate_event(topic, payload):
    global race_state

    timestamp = parse_timestamp(payload)

    print(f"{timestamp} received from payload {payload}", flush=True)

    if "start" in topic:
        if not race_state["start_time"]:
            race_state["start_time"] = timestamp
            race_state["running"] = True
            race_state["delta"] = None
            add_mqtt_log(f"[RACE] Start triggered at {timestamp.time()}")

    elif "finish" in topic:
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
# ----------------------
# Agents
# ----------------------
class ReceiverAgent(Agent):
    class ReceiveMessageBehaviour(CyclicBehaviour):

        async def run(self):
            timeout = 10
            print("Waiting for message...", flush=True)
            msg = await self.receive(timeout=timeout)  # wait for a message for 10 seconds
            if msg:
                robot_id = msg.metadata.get("robot_id", "unknown")
                type_msg = msg.metadata.get("type", "unknown")
                if type_msg == "image":
                    print(f"Received image from {robot_id}", flush=True)
                    latest_frames[robot_id] = msg.body
                    log_entry = f"Image received from {robot_id}"
                    add_log(robot_id, log_entry)
                elif type_msg == "log":
                    log_entry = f"From {msg.sender}: {msg.body}"
                    print(f"Log added : {log_entry}", flush=True)
                    add_log(robot_id, log_entry)
                else:
                    print(f"Unknown message type: {type_msg}", flush=True)
                    add_log(robot_id, f"Unknown message type: {type_msg}")
            else:
                print(f"Did not received any message after {timeout} seconds")
                # self.kill()

        async def on_end(self):
            await self.agent.stop()

    async def setup(self):
        print("ReceiverAgent started setup", flush=True)
        b = self.ReceiveMessageBehaviour()
        self.add_behaviour(b)

class SenderAgent(Agent):
    class SendBehaviour(OneShotBehaviour):
        def __init__(self, robot_id, message):
            super().__init__()
            self.robot_id = robot_id
            self.message = message
        async def run(self):
            msg = spade.message.Message(
                to="receiverClient@prosody",
                body=self.message
            )
            msg.set_metadata("robot_id", self.robot_id)
            msg.set_metadata("type", "log")
            print(f"Sending message: {msg.body}", flush=True)
            await self.send(msg)

def start_agent():
    async def agent_task():
        xmpp_username = "receiverClient"
        xmpp_server = "prosody"
        xmpp_password = os.getenv("XMPP_PASSWORD", "plsnohack")

        receiver = ReceiverAgent(f"{xmpp_username}@{xmpp_server}", xmpp_password)
        await receiver.start(auto_register=True)
        await spade.wait_until_finished(receiver)

    asyncio.run(agent_task())

# ----------------------
# MQTT Client
# ----------------------
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}", flush=True)
    for topic, qos in MQTT_TOPICS:
        client.subscribe(topic)
        print(f"Subscribed to {topic}", flush=True)

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    log_entry = f"[MQTT:{topic}] {payload}"
    add_mqtt_log(log_entry)
    print(log_entry, flush=True)

    if "start" in topic or "finish" in topic:
        handle_gate_event(topic, payload)

def start_mqtt_client():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

#  ----

mqtt_pub_client = mqtt.Client()
mqtt_pub_client.connect(MQTT_BROKER, MQTT_PORT)

def send_mqtt_command(topic, command):
    mqtt_pub_client.publish(topic, command)
    print(f"Published to {topic}: {command}")


# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    threading.Thread(target=start_agent, daemon=True).start()
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    app.run(host="0.0.0.0", port=8050, debug=True)
