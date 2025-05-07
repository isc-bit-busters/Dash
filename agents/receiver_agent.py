from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from utils.log_utils import add_log, add_arm_log
from utils.log_utils import latest_frames, latest_path_frames
import asyncio
import spade
import utils.connection_status as conn_status

class ReceiverAgent(Agent):
    class ReceiveMessageBehaviour(CyclicBehaviour):
        async def run(self):
            timeout = 10
            print("Waiting for message...", flush=True)
            msg = await self.receive(timeout=timeout)

            if not msg:
                print(f"Did not receive any message after {timeout} seconds")
                return
            
            robot_id = msg.metadata.get("robot_id", "unknown")
            type_msg = msg.metadata.get("type", "unknown")

            handlers = {
                "image": lambda: self.handle_image(robot_id, msg.body),
                "log": lambda: self.handle_log(robot_id, msg.sender, msg.body),
                "cube_detection": lambda: self.handle_cube_detection(robot_id, msg.body),
                "arm_log": lambda: self.handle_arm_log(msg.body),
                "path_image": lambda: self.handle_path_image(robot_id, msg.body),
            }

            handler = handlers.get(type_msg)
            if handler:
                handler()
            else:
                print(f"Unknown message type: {type_msg}", flush=True)
                add_log(robot_id, f"Unknown message type: {type_msg}")

        def handle_image(self, robot_id, body):
            print(f"Received image from {robot_id}", flush=True)
            latest_frames[robot_id] = body
            add_log(robot_id, f"Image received from {robot_id}")

        def handle_log(self, robot_id, sender, body):
            log_entry = f"From {sender}: {body}"
            print(f"Log added : {log_entry}", flush=True)
            add_log(robot_id, body)

        def handle_cube_detection(self, robot_id, body):
            print(f"Received cube detection data from {robot_id} {body}", flush=True)
            add_log(robot_id, f"Cube detection data: {body}")

        def handle_arm_log(self, body):
            print(f"Received arm log: {body}", flush=True)
            add_arm_log(body)

        def handle_path_image(self, robot_id, body):
            print(f"Received path image from {robot_id}", flush=True)
            latest_path_frames[robot_id] = body
            add_log(robot_id, f"Path image received from {robot_id}")

        async def on_end(self):
            await self.agent.stop()
            conn_status.set_xmpp_connected(False)

    async def setup(self):
        print("ReceiverAgent started setup", flush=True)
        self.add_behaviour(self.ReceiveMessageBehaviour())

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
        from config import XMPP_USERNAME, XMPP_SERVER, XMPP_PASSWORD
        try:
            receiver = ReceiverAgent(f"{XMPP_USERNAME}@{XMPP_SERVER}", XMPP_PASSWORD)
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
