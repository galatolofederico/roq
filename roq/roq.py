import os
import sys
import pickle
import asyncio
import logging

from roq import _config

logger = logging.getLogger(__name__)

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
