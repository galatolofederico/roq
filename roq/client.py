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

    async def init(self):
        for topic in self.args_bindings:
            async def handle(message):
                payload = message.payload
                fn = self.args_bindings[topic]["fn"]
                return_topic = self.args_bindings[topic]["return_topic"]

                result = fn(*pickle.loads(payload))

                payload = pickle.dumps(result)
                logger.debug(f"ROQClient.handle (of {topic}): Publishing on '{return_topic}'")
                await self.client.publish(return_topic, payload=payload)

            logger.debug(f"ROQClient.init: Binding handler function to '{topic}'")
            await self.client.subscribe(topic)
            self.client._queue.bind_function(topic, handle)

    async def call(self, topic, *args, **kwargs):
        args_topic = os.path.join(topic, "args")
        return_topic = os.path.join(topic, "return")

        if return_topic not in self.return_queues:
            self.return_queues[return_topic] = asyncio.Queue()
        
        logger.debug(f"ROQClient.call on '{topic}': Binding return queue to '{return_topic}'")
        await self.client.subscribe(return_topic)
        self.client._queue.bind_queue(return_topic, self.return_queues[return_topic])
        
        payload = pickle.dumps(args)
        logger.debug(f"ROQClient.call on '{topic}': Publishing on '{args_topic}'")
        await self.client.publish(args_topic, payload=payload)
        
        payload = await self.return_queues[return_topic].get()
        return pickle.loads(payload.payload)

