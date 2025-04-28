from dash import html, dcc
import dash_bootstrap_components as dbc

from utils.mac_utils import load_mac_addresses

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

def create_gates_settings():
    mac_addresses = load_mac_addresses()
    return dbc.Accordion([
        dbc.AccordionItem([
            dbc.Form([
                html.H5("Gate 1 Settings"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Start Gate MAC"),
                        dbc.Input(id="gate1-start-mac", type="text", value=mac_addresses.get("gate1_start", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ]),
                    dbc.Col([
                        dbc.Label("Finish Gate MAC"),
                        dbc.Input(id="gate1-finish-mac", type="text", value=mac_addresses.get("gate1_finish", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ])
                ]),
                dbc.Button("Send Gate 1 MACs", id="send-gate1-macs", color="primary", className="mt-3"),
                html.Div(id="gate1-mac-status", className="mt-2", style={"fontWeight": "bold"}),
                html.Hr(),

                html.H5("Gate 2 Settings"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Start Gate MAC"),
                        dbc.Input(id="gate2-start-mac", type="text", value=mac_addresses.get("gate2_start", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ]),
                    dbc.Col([
                        dbc.Label("Finish Gate MAC"),
                        dbc.Input(id="gate2-finish-mac", type="text", value=mac_addresses.get("gate2_finish", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ])
                ]),
                dbc.Button("Send Gate 2 MACs", id="send-gate2-macs", color="primary", className="mt-3"),
                html.Div(id="gate2-mac-status", className="mt-2", style={"fontWeight": "bold"})
            ])
        ], title="Gates Settings")
    ], start_collapsed=True, always_open=True)

def mqtt_log_card():
    return dbc.Card([
        dbc.CardHeader("Latest Race Logs"),
        dbc.CardBody([
            html.Ul(id="mqtt-log-display", className="log-list", style={"maxHeight": "300px", "overflowY": "scroll"})
        ])
    ])

def race_timer():
    return [
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
    ]

def top_camera_layout():
    return [
        html.H5("Top Camera View", className="my-4 text-center"),
        dbc.Row([
            dbc.Col(html.Img(id="top-camera-image", style={"width": "100%", "maxHeight": "600px"})),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(dbc.Button("Capture New Image", id="capture-top-image-btn", color="primary")),
        ], className="text-center"),
        dbc.Row([
            html.Div(id="capture-status", className="mt-2", style={"fontWeight": "bold", "color": "green"})
        ]),
    ]

connection_status_card = dbc.Card([
    dbc.CardHeader("Connection Status"),
    dbc.CardBody([
        html.P(id="mqtt-status"),
        html.P(id="xmpp-status"),
    ])
], id="connection-status-card", className="mb-4")


layout = dbc.Container([
    html.H1("Robot Control Dashboard", className="my-4 text-center"),
    connection_status_card,

    *top_camera_layout(),

    dbc.Row([
        dbc.Col(robot_card("robot1"), md=6),
        dbc.Col(robot_card("robot2"), md=6)
    ]),
    html.Hr(),
    *race_timer(),
    html.Hr(),
    mqtt_log_card(),
    html.Hr(),
    create_gates_settings(),
    
    html.Div(id="mqtt-command-status"),
    dbc.Button("Send MQTT Reset", id="send-mqtt-btn", color="secondary", className="mt-3"),
    dcc.Interval(id='update-interval', interval=100, n_intervals=0),
    dcc.Interval(id='robot1-penalty-cooldown', interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id='robot2-penalty-cooldown', interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="reset-race-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="capture-status-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="gate1-mac-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="gate2-mac-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="mqtt-command-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
], fluid=True)
