import asyncio
import os
import logging
import pickle
import random

logger = logging.getLogger(__name__)

class ROQClient:
    def __init__(self, client, args_bindings):
        self.return_queues = dict()
        self.args_bindings = args_bindings

        self.client = client

    async def init(self):
        for topic in self.args_bindings:
            async def handle(payload):
                fn = self.args_bindings[topic]["fn"]
                return_topic = self.args_bindings[topic]["return_topic"]
                
                payload = pickle.loads(payload.payload)
                args = payload["args"]
                kwargs = payload["kwargs"]
                nonce = payload["nonce"]

                result = fn(*args, **kwargs)

                payload = pickle.dumps(dict(
                    result=result,
                    nonce=nonce
                ))
                logger.debug(f"ROQClient.handle (of {topic}): Publishing on '{return_topic}'")
                await self.client.publish(return_topic, payload=payload)

            logger.debug(f"ROQClient.init: Binding handler function to '{topic}'")
            await self.client.subscribe(topic)
            self.client._queue.bind_function(topic=topic, fn=handle)

    async def call(self, topic, *args, **kwargs):
        args_topic = os.path.join(topic, "args")
        return_topic = os.path.join(topic, "return")
        nonce = random.randint(0, 2**32)
        queue = asyncio.Queue()
        
        logger.debug(f"ROQClient.call on '{topic}': Binding return queue to '{return_topic}'")
        await self.client.subscribe(return_topic)
        self.client._queue.bind_queue(topic=return_topic, queue=queue, nonce=nonce)
        
        payload = pickle.dumps(dict(
            args=args,
            kwargs=kwargs,
            nonce=nonce
        ))
        logger.debug(f"ROQClient.call on '{topic}': Publishing on '{args_topic}'")
        await self.client.publish(args_topic, payload=payload)
        
        result = await queue.get()
        logger.debug(f"ROQClient.call on '{topic}': Received result from RPC: {result}")

        self.client._queue.unbind_queue(topic=return_topic)
        logger.debug(f"ROQClient.call on '{topic}': Unbound return queue from '{return_topic}'")

        return result