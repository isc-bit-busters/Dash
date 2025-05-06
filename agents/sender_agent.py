from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
import asyncio
import os
import threading
import utils.connection_status as conn_status

class SenderAgent(Agent):
    class SendBehaviour(OneShotBehaviour):
        def __init__(self, robot_id, message, msg_type="log"):
            super().__init__()
            self.robot_id = robot_id
            self.message = message
            self.msg_type = msg_type

        async def run(self):
            from spade.message import Message
            to = f"{self.robot_id}@prosody"
            msg = Message(
                to=to,
                body=self.message
            )
            print(f"Sending message to {to}: {self.message}", flush=True)
            msg.set_metadata("robot_id", self.robot_id)
            msg.set_metadata("type", self.msg_type)
            await self.send(msg)

    async def on_connection_failed(self, reason):
        conn_status.set_xmpp_connected(False)
        print(f"⚠️ SenderAgent connection failed: {reason}", flush=True)

    async def on_disconnected(self):
        conn_status.set_xmpp_connected(False)
        print("⚠️ SenderAgent got disconnected.", flush=True)

def send_message_to_robot(robot_id, message, sender_id="testClient", msg_type="log"):
    def _send():
        async def task():
            password = os.getenv("XMPP_PASSWORD", "plsnohack")
            try:
                sender = SenderAgent(f"{sender_id}@prosody", password)
                await sender.start(auto_register=True)
                conn_status.set_xmpp_connected(True)
                sender.add_behaviour(sender.SendBehaviour(robot_id, message, msg_type))
                await asyncio.sleep(10)
                await sender.stop()
                print("✅ SenderAgent finished and stopped.", flush=True)
            except Exception as e:
                conn_status.set_xmpp_connected(False)
                print(f"⚠️ Could not start/send with SenderAgent: {e}", flush=True)

        try:
            asyncio.run(task())
        except Exception as e:
            conn_status.set_xmpp_connected(False)
            print(f"⚠️ Fatal error during SenderAgent send: {e}", flush=True)

    threading.Thread(target=_send, daemon=True).start()