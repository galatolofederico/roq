# roq 

Pythonic RPC over MQTT for [aiomqtt](https://github.com/sbtinstruments/aiomqtt)

- 💡 Clean interface, RPC with just a decorator
- 💪 Robust multi-client implementation using
- 🤝 Seamlessly integrates with [aiomqtt](https://github.com/sbtinstruments/aiomqtt)


## Quick start

**Server Side:** Expose a function over MQTT:

```python
import roq

@roq.procedure("/your/topic/name")
def sum(a, b):
    return a + b
```

**Client Side:** Call that function over MQTT:

```python
import roq

async with client:
    ret = await client["/rpc/sum"](1, 2)
```

## installation

```
pip install roq
```

## Usage

To create a `roq`-enabled `aiomqtt.Client` you can:

1) Replace `aiomqtt.Client` with `roq.Client` in your code:

```python
import roq

client = roq.Client(
    ...  # Your usual MQTT client setup
)

async with client:
    # Call RPCs, subscribe, handle messages, the usual stuff
    await client["/your/topic/name"](some, argument, some=keyword)
    await client.subscribe("/some/other/topic")

    async for message in client.messages:
        print("Received message on topic", message.topic) 
```

2) Wrap an existing `aiomqtt.Client` with `roq.Client` (`queue_type` must be an instance of `roq.ROQRouterQueue`)

```python
import roq
import aiomqtt

client = aiomqtt.Client(
    ...  # Setup here
    queue_type=roq.ROQRouterQueue
)

async with roq.Client(client) as client:
    # Same as above, subscribe, call, handle
```

Use the `roq.procedure("/topic/name")` decorator to bind a function to be called on `/topic/name`.

Use `client["/topic/name"](your, arguments, oreven=keywoardargs)` to call a function bound to `/topic/name`

## Examples

`server.py`:

```python
import roq
import asyncio

@roq.procedure("/rpc/sum")
def sum(a, b):
    return a + b

async def main():
    client = roq.Client("test.mosquitto.org")
    
    async with client:
        await client.subscribe("/some/other/topic")
        async for message in client.messages:
            print("Received message on topic", message.topic)

if __name__ == "__main__":
    asyncio.run(main())
```

`client.py`:

```python
import roq
import asyncio

async def main():
    client = roq.Client("test.mosquitto.org")

    async with client:
        ret = await client["/rpc/sum"](1, 2)
        print(f"Result from RPC: {ret}")
        await client.publish("/some/other/topic", payload=b"Hello, World!")

if __name__ == "__main__":
    asyncio.run(main())
```


## Use a custom queue

You can use a custom queue extending `roq.ROQRouterQueue`

```python
class YourQueue(row.ROQRouterQueue):
    def _put(self, item):
        if self.handle_roq_message(item): return   # you must add this line

        #your item logic here
        super()._put(item)

    def _get(self):
        return super()._get()
```

## License

This project is licensed under the Apache License 2.0. For more details, see the LICENSE file in the root directory of this project or check out the Apache License 2.0 [here](https://www.apache.org/licenses/LICENSE-2.0)