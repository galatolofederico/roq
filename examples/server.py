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