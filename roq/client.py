import asyncio
import os
import logging
import pickle

logger = logging.getLogger(__name__)

class ROQClient:
    def __init__(self, client, args_bindings):
        self.return_queues = dict()
        self.args_bindings = args_bindings

        self.client = client

    async def call(self, topic, *args, **kwargs):
        args_topic = os.path.join(topic, "args")
        return_topic = os.path.join(topic, "return")

        if return_topic not in self.return_queues:
            self.return_queues[return_topic] = asyncio.Queue()
            logger.debug(f"ROQClient.call on '{topic}': Subscribing to '{return_topic}'")
            await self.client.subscribe(return_topic)
            import time
            time.sleep(0.1)
        
        self.client._queue.bind(return_topic, self.return_queues[return_topic])

        payload = pickle.dumps(args)
        logger.debug(f"ROQClient.call on '{topic}': Publishing on '{args_topic}'")
        await self.client.publish(args_topic, payload=payload)
        
        payload = await self.return_queues[return_topic].get()
        return pickle.loads(payload.payload)
    
    async def handle(self, message):
        global _config

        topic = str(message.topic)
        payload = message.payload

        logger.debug(f"ROQClient.handle: Received message on '{topic}'")

        if topic in self.args_bindings:
            logger.debug(f"ROQClient.handle: '{topic}' is a procedure")
            fn = self.args_bindings[topic]["fn"]
            return_topic = self.args_bindings[topic]["return_topic"]

            result = fn(*pickle.loads(payload))

            payload = pickle.dumps(result)
            logger.debug(f"ROQClient.handle: Publishing on '{return_topic}'")
            await self.client.publish(return_topic, payload=payload)
            return True
        
        return False
    
    async def dispatch(self):
        async with asyncio.TaskGroup() as tg:
            async for message in self.client.messages:
                tg.create_task(self.handle(message))
