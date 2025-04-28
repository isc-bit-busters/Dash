import dash
import dash_bootstrap_components as dbc

from layout import layout
from callbacks import register_callbacks
from agents.receiver_agent import start_receiver_agent
from mqtt.mqtt_client import start_mqtt_client, init_mqtt_pub_client

import threading

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Multi-Robot Dashboard"
app.layout = layout

# Register all callbacks
register_callbacks(app)

if __name__ == "__main__":
    threading.Thread(target=start_receiver_agent, daemon=True).start()
    threading.Thread(target=start_mqtt_client, daemon=True).start()
    init_mqtt_pub_client()
    app.run(host="0.0.0.0", port=8050, debug=True)
