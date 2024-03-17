import asyncio
import logging
import pickle

logger = logging.getLogger(__name__)

class ROQRouterQueue(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue_bindings = dict()
        self.function_bindings = dict()

    def bind_queue(self, *, topic, queue, nonce):
        assert isinstance(queue, asyncio.Queue)
        assert isinstance(topic, str)
        
        self.queue_bindings[topic] = dict(
            queue=queue,
            nonce=nonce
        )

    def unbind_queue(self, *, topic):
        assert isinstance(topic, str)
        
        if topic in self.queue_bindings:
            del self.queue_bindings[topic]

    def bind_function(self, *, topic, fn):
        assert callable(fn)
        assert isinstance(topic, str)
        
        self.function_bindings[topic] = fn

    def handle_roq_message(self, item):
        topic = str(item.topic)
        if topic in self.queue_bindings:
            logger.debug(f"ROQRouterQueue._put: '{topic}' is bound to a queue")
            payload = pickle.loads(item.payload)

            result = payload["result"]
            nonce = payload["nonce"]

            if nonce != self.queue_bindings[topic]["nonce"]:
                print(nonce, self.queue_bindings[topic]["nonce"])
                logger.debug(f"ROQRouterQueue._put: Received message on '{topic}' with invalid nonce, discarding")
            else:
                self.queue_bindings[topic]["queue"].put_nowait(result)
            return True

        elif topic in self.function_bindings:
            logger.debug(f"ROQRouterQueue._put: '{topic}' is bound to a function")
            fn = self.function_bindings[topic]
            asyncio.create_task(fn(item))
            return True
        
        return False

    def _put(self, item):
        logger.debug(f"ROQRouterQueue._put: Received message on '{item.topic}'")
        if self.handle_roq_message(item): return
        super()._put(item)

    def _get(self):
        return super()._get()