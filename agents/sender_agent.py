from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
import asyncio
import os
import threading

class SenderAgent(Agent):
    class SendBehaviour(OneShotBehaviour):
        def __init__(self, robot_id, message):
            super().__init__()
            self.robot_id = robot_id
            self.message = message

        async def run(self):
            from spade.message import Message
            msg = Message(
                to="receiverClient@prosody",
                body=self.message
            )
            msg.set_metadata("robot_id", self.robot_id)
            msg.set_metadata("type", "log")
            await self.send(msg)

def send_message_to_robot(robot_id, message, sender_id="testClient"):
    def _send():
        async def task():
            password = os.getenv("XMPP_PASSWORD", "plsnohack")
            sender = SenderAgent(f"{sender_id}@prosody", password)
            await sender.start(auto_register=True)
            sender.add_behaviour(sender.SendBehaviour(robot_id, message))
            await asyncio.sleep(5)
            await sender.stop()

        asyncio.run(task())

    threading.Thread(target=_send, daemon=True).start()
