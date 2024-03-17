import asyncio
import logging

logger = logging.getLogger(__name__)

class ROQRouterQueue(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_bindings = dict()
        self.function_bindings = dict()

    def bind_queue(self, topic, queue):
        assert isinstance(queue, asyncio.Queue)
        assert isinstance(topic, str)
        
        self.queue_bindings[topic] = queue

    def bind_function(self, topic, fn):
        assert callable(fn)
        assert isinstance(topic, str)
        
        self.function_bindings[topic] = fn

    def _put(self, item):
        topic = str(item.topic)
        logger.debug(f"ROQRouterQueue._put: Received message on '{topic}'")
        if topic in self.queue_bindings:
            logger.debug(f"ROQRouterQueue._put: '{topic}' is bound to a queue")
            self.queue_bindings[topic].put_nowait(item)
        elif topic in self.function_bindings:
            logger.debug(f"ROQRouterQueue._put: '{topic}' is bound to a function")
            fn = self.function_bindings[topic]
            asyncio.create_task(fn(item))
        else:
            super()._put(item)

    def _get(self):
        return super()._get()