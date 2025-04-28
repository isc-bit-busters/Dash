from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from utils.log_utils import add_log
from utils.log_utils import latest_frames
import asyncio
import os
import time
import threading
import utils.connection_status as conn_status

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
            conn_status.set_xmpp_connected(False)

    async def setup(self):
        print("ReceiverAgent started setup", flush=True)
        b = self.ReceiveMessageBehaviour()
        self.add_behaviour(b)

    async def on_connection_failed(self, reason):
        """Called automatically when connection to server is lost."""
        conn_status.set_xmpp_connected(False)
        print(f"⚠️ ReceiverAgent connection failed: {reason}", flush=True)

    async def on_disconnected(self):
        """Optional: handle clean disconnection."""
        conn_status.set_xmpp_connected(False)
        print("⚠️ ReceiverAgent got disconnected.", flush=True)

receiver = None

def start_receiver_agent():
    """Start ReceiverAgent with auto-reconnect in background."""

    def receiver_loop():
        global receiver

        while True:
            if not receiver:
                async def task():
                    username = "receiverClient"
                    password = os.getenv("XMPP_PASSWORD", "plsnohack")
                    try:
                        receiver = ReceiverAgent(f"{username}@prosody", password)
                        await receiver.start(auto_register=True)
                        conn_status.set_xmpp_connected(True)
                        print("✅ Receiver Agent started", flush=True)
                    except Exception as e:
                        conn_status.set_xmpp_connected(False)
                        print(f"⚠️ Could not start XMPP Receiver Agent: {e}", flush=True)

                try:
                    asyncio.run(task())
                except Exception as e:
                    conn_status.set_xmpp_connected(False)
                    print(f"⚠️ Fatal error in XMPP receiver agent: {e}", flush=True)
                    receiver = None

            else:
                if not conn_status.is_xmpp_connected():
                    print("⚠️ Receiver agent connection lost. Trying to reconnect...", flush=True)
                    receiver = None  # Force recreation

            time.sleep(15)  # Check every 5 seconds

    threading.Thread(target=receiver_loop, daemon=True).start()