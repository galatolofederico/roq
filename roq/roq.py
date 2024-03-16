import os
import pickle
import asyncio

_config = dict(
    bindings=dict()
)

class ROQClient:
    def __init__(self, client):
        global _config
        self.return_queues = dict()
        self.args_topics = list()

        self.client = client

    async def call(self, topic, *args, **kwargs):
        args_topic = os.path.join(topic, "args")
        return_topic = os.path.join(topic, "return")

        if return_topic not in self.return_queues:
            self.return_queues[return_topic] = asyncio.Queue()
        
        payload = pickle.dumps(args)
        await self.client.publish(args_topic, payload=payload)
        
        return await self.return_queues[return_topic].get()
    
    async def handle(self, message):
        topic = message.topic
        payload = message.payload

        if topic in self.args_topics:
            fn = _config["bindings"][topic]["fn"]
            return_topic = _config["bindings"][topic]["return_topic"]

            result = fn(*pickle.loads(payload))

            payload = pickle.dumps(result)
            await self.client.publish(return_topic, payload=payload)
            return True
        
        elif topic in self.return_queues:
            self.return_queues[topic].put(pickle.loads(payload))
            return True

        return False
    
    async def dispatch(self):
        async for message in self.client.messages:
            await self.handle(message)

async def bind(client):
    global _config

    for topic in _config["bindings"]:
        await client.subscribe(topic)

    return ROQClient(client)

def procedure(topic):
    global _config

    if topic in _config["bindings"]:
        raise Exception(f"Topic {topic} is already bound to a procedure")

    args_topic = os.path.join(topic, "args")
    return_topic=os.path.join(topic, "return")
    def decorator(fn):
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        _config["bindings"][args_topic] = dict(
            fn=fn,
            return_topic=return_topic,
        )

        return wrapper
    
    return decorator
