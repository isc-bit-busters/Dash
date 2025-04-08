import dash
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import time
import threading
from collections import deque
import numpy as np
import cv2
import base64

# ----------------------
# Globals
# ----------------------
robot_logs = {
    'robot1': deque(maxlen=10),
    'robot2': deque(maxlen=10)
}

robot_states = {
    'robot1': False,
    'robot2': False
}

latest_frames = {
    'robot1': None,
    'robot2': None
}

# ----------------------
# Simulated Data Threads
# ----------------------
def generate_logs(robot_id):
    while True:
        if robot_states[robot_id]:
            robot_logs[robot_id].appendleft(f"{robot_id} log at {time.strftime('%H:%M:%S')}")
        time.sleep(2)

def generate_black_image(robot_id):
    while True:
        # Create black image
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(buffer).decode()
        latest_frames[robot_id] = img_base64
        time.sleep(0.05)

# Start background threads
for rid in ['robot1', 'robot2']:
    threading.Thread(target=generate_logs, args=(rid,), daemon=True).start()
    threading.Thread(target=generate_black_image, args=(rid,), daemon=True).start()

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
                dbc.Col(dbc.Button("Stop", id=f"{robot_id}-stop", color="danger"))
            ])
        ])
    ], className="mb-4")

app.layout = dbc.Container([
    html.H1("Robot Control Dashboard", className="my-4 text-center"),
    dbc.Row([
        dbc.Col(robot_card("robot1"), md=6),
        dbc.Col(robot_card("robot2"), md=6)
    ]),
    dcc.Interval(id='update-interval', interval=1000, n_intervals=0)
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
    Input('update-interval', 'n_intervals')
)
def update_ui(n):
    r1_logs = [html.Li(log) for log in list(robot_logs['robot1'])]
    r2_logs = [html.Li(log) for log in list(robot_logs['robot2'])]

    r1_img = f"data:image/jpeg;base64,{latest_frames['robot1']}" if latest_frames['robot1'] else ""
    r2_img = f"data:image/jpeg;base64,{latest_frames['robot2']}" if latest_frames['robot2'] else ""

    return r1_logs, r2_logs, r1_img, r2_img

# Fix scoping with wrapper
def make_toggle_callback(robot_id):
    def toggle(start_clicks, stop_clicks, is_start_disabled):
        triggered_id = dash.ctx.triggered_id
        if triggered_id and triggered_id.endswith('start'):
            robot_states[robot_id] = True
            return True, False
        elif triggered_id and triggered_id.endswith('stop'):
            robot_states[robot_id] = False
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

# ----------------------
# Run App
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
