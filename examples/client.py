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