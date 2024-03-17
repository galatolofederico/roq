import asyncio
import os
import logging
import pickle
import random
from aiomqtt import Client as MQTTClient

from roq.router import ROQRouterQueue
from roq import _config

logger = logging.getLogger(__name__)

class Client:
    def __init__(self, *args, **kwargs):
        self.return_queues = dict()

        if len(args) == 1 and isinstance(args[0], MQTTClient):
            self.client = args[0]
        else:
            kwargs["queue_type"] = ROQRouterQueue
            self.client = MQTTClient(*args, **kwargs)

        if not isinstance(self.client._queue, ROQRouterQueue):
            raise Exception("Client's queue must be of type ROQRouterQueue. Use roq.Client to create the client or use 'queue_type=roq.ROQRouterQueue' when creating the client using aiomqtt.Client")

    async def __aenter__(self):
        await self.client.__aenter__()
        await self.init(_config["bindings"])
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.client.__aexit__(exc_type, exc, tb)

    def __aiter__(self):
        return self.inner.__aiter__()

    async def init(self, bindings):
        for topic in bindings:
            async def handle(payload):
                fn = bindings[topic]["fn"]
                return_topic = bindings[topic]["return_topic"]
                
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
    
    def __getattr__(self, name):
        return getattr(self.client, name)

    def __getitem__(self, topic):
        def wrapper(*args, **kwargs):
            return self.call(topic, *args, **kwargs)
        return wrapper