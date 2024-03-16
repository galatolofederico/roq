import os
import sys
import pickle
import asyncio
import logging

from roq.client import ROQClient

logger = logging.getLogger(__name__)

_config = dict(
    bindings=dict()
)

async def bind(client):
    global _config

    for topic in _config["bindings"]:
        logger.debug(f"bind: Subscribing to '{topic}'")
        await client.subscribe(topic)

    return ROQClient(client, args_bindings=_config["bindings"].copy())

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
