import asyncio

class ROQRouterQueue(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bindings = dict()

    def bind(self, topic, queue):
        self.bindings[topic] = queue

    def _put(self, item):
        topic = str(item.topic)
        if topic in self.bindings:
            self.bindings[topic].put_nowait(item)
        else:
            super()._put(item)

    def _get(self):
        return super()._get()