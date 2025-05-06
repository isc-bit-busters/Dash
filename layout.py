from dash import html, dcc
import dash_bootstrap_components as dbc

from utils.mac_utils import load_mac_addresses

from config import ROBOT_NAMES, TOP_CAMERA_NAME

def robot_card(robot_id):
    return dbc.Card([
        dbc.CardHeader(html.H4(f"{robot_id.upper()}")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(html.Img(id=f"{robot_id}-image", style={
                    "maxWidth": "100%",
                    "height": "auto",
                    "maxHeight": "400px",
                    "objectFit": "contain",
                    "border": "1px solid #ccc"
                }), md=6),
                dbc.Col([
                    html.H5("Logs"),
                    html.Ul(id=f"{robot_id}-logs", className="log-list")
                ], md=6),
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col(dbc.Button("Calibrate", id=f"{robot_id}-calibrate", color="primary", className="me-2")),
                dbc.Col([
                    dbc.Button("Penalty", id=f"{robot_id}-penalty", color="warning", n_clicks=0),
                    html.Div(id=f"{robot_id}-penalty-status", className="mt-2", style={"color": "green", "fontWeight": "bold"})
                ]),
                html.Div(id=f"{robot_id}-penalty-count", className="mt-2", style={"fontWeight": "bold", "color": "red"}),
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
                        dbc.Label("Start Gate 1 MAC"),
                        dbc.Input(id="gate1-start-mac", type="text", value=mac_addresses.get("gate1_start", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ]),
                    dbc.Col([
                        dbc.Label("Finish Gate 1 MAC"),
                        dbc.Input(id="gate1-finish-mac", type="text", value=mac_addresses.get("gate1_finish", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ]),
                    dbc.Col([
                        dbc.Label("Start Gate 2 MAC"),
                        dbc.Input(id="gate2-start-mac", type="text", value=mac_addresses.get("gate2_start", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ]),
                    dbc.Col([
                        dbc.Label("Finish Gate 2 MAC"),
                        dbc.Input(id="gate2-finish-mac", type="text", value=mac_addresses.get("gate2_finish", ""), placeholder="XX:XX:XX:XX:XX:XX")
                    ])
                ]),
                dbc.Button("Send Gate MACs", id="send-gate-macs", color="primary", className="mt-3"),
                html.Div(id="gate-mac-status", className="mt-2", style={"fontWeight": "bold"}),
                html.Div([
                    html.Span("Gate 1 Start: "), html.Span(id="gate1-start-status"),
                    html.Span(" | Gate 1 Finish: "), html.Span(id="gate1-finish-status"),
                    html.Span(" | Gate 2 Start: "), html.Span(id="gate2-start-status"),
                    html.Span(" | Gate 2 Finish: "), html.Span(id="gate2-finish-status"),
                ], className="mt-3", style={"fontWeight": "bold", "fontSize": "1.2em"}),
                html.Hr(),
            ])
        ], title="Gates Settings")
    ], start_collapsed=True, always_open=True)

def robotic_arm_card():
    return dbc.Accordion([
        dbc.AccordionItem([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Command Type"),
                    dcc.Dropdown(
                        id="xmpp-command-type",
                        options=[
                            {"label": t, "value": t} for t in [
                                "set_host_ip",
                                "point", "trajectory", 
                                "activate_gripper", "open_gripper", "close_gripper", 
                                "set_speed", "set_acceleration"
                            ]
                        ],
                        placeholder="Select a command"
                    )
                ])
            ]),
            dbc.Label("Command Body (JSON or string)"),
            dbc.Textarea(id="xmpp-command-body", placeholder='E.g. 10.30.5.159, [0.3, 0.2, 0.26, 0, 0, -1] or leave empty for gripper'),
            dbc.Button("Send XMPP Command", id="send-xmpp-command-btn", color="primary", className="mt-2"),
            html.Div(id="xmpp-command-status", className="mt-2", style={"fontWeight": "bold"}),
            html.Hr(),
            html.H5("Received Messages"),
            html.Ul(id="robotic-arm-log-display", style={"maxHeight": "200px", "overflowY": "scroll"})
        ], title="Robotic Arm Command")
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
        dbc.Row([
            dbc.Col(
                html.Img(
                    id=f"{TOP_CAMERA_NAME}-image",
                    style={
                        "height": "100%",
                        "width": "auto",
                        "objectFit": "contain",
                        "display": "block",
                        "margin": "0 auto"
                    }
                ),
                style={"height": "40vh"}
            ),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col(
                dbc.ButtonGroup([
                    dbc.Button("Capture New Image", id="capture-top-image-btn", color="primary"),
                    dbc.Button("Validate", id="validate-top-image-btn", color="primary"),
                ]),
                width="auto", className="text-center"
            )
        ], className="text-center"),
        dbc.Row([
            html.Div(id="capture-status", className="mt-2", style={"fontWeight": "bold", "color": "green"})
        ]),
    ]

def start_stop_buttons():
    return dbc.Row([
        dbc.Col(
            dbc.ButtonGroup([
                dbc.Button("Start", id="robots-start", color="success"),
                dbc.Button("Stop", id="robots-stop", color="danger", disabled=True),
            ]),
            width="auto", className="text-center"
        )
    ], className="text-center mb-4")

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
    dbc.Col(robot_card(robot_id), md=6) for robot_id in ROBOT_NAMES
    ]),
    start_stop_buttons(),
    html.Hr(),
    *race_timer(),
    html.Hr(),
    mqtt_log_card(),
    html.Hr(),
    create_gates_settings(),
    html.Hr(),
    robotic_arm_card(),
    
    html.Div(id="mqtt-command-status"),
    dcc.Interval(id='update-interval', interval=100, n_intervals=0),
    *[dcc.Interval(id=f'{robot_id}-penalty-cooldown', interval=1500, n_intervals=0, max_intervals=1) for robot_id in ROBOT_NAMES],
    dcc.Interval(id="reset-race-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="capture-status-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="gate-mac-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
    dcc.Interval(id="mqtt-command-clear-interval", interval=3000, n_intervals=0, max_intervals=1),
], fluid=True)
