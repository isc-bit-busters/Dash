from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from utils.log_utils import add_log, add_arm_log
from utils.log_utils import latest_frames
import os
import asyncio
import spade
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
                elif type_msg == "cube_detection":
                    cube_data = msg.body
                    print(f"Received cube detection data from {robot_id} {cube_data}", flush=True)
                    add_log(robot_id, f"Cube detection data: {cube_data}")
                elif type_msg == "arm_log":
                    print(f"Received arm log: {msg.body}", flush=True)
                    add_arm_log(msg.body)
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

def start_agent():
    async def agent_task():
        xmpp_username = "receiverClient"
        xmpp_server = "prosody"
        xmpp_password = os.getenv("XMPP_PASSWORD", "plsnohack")
        try:
            receiver = ReceiverAgent(f"{xmpp_username}@{xmpp_server}", xmpp_password)
            await receiver.start(auto_register=True)
            conn_status.set_xmpp_connected(True)
            print("ReceiverAgent started", flush=True)
            await spade.wait_until_finished(receiver)
        except spade.exception.XMPPError as e:
            print(f"XMPP Error: {e}", flush=True)
            conn_status.set_xmpp_connected(False)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            conn_status.set_xmpp_connected(False)

    asyncio.run(agent_task())
