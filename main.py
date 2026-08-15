import asyncio

from analysis.capture import Capture
from analysis.pipeline import Pipeline
from analysis.publisher import Publisher


async def main():
    publisher = Publisher()
    await publisher.connect()
    pipeline = Pipeline(publisher=publisher)
    capture = Capture(pipeline)
    try:
        await capture.run()
    finally:
        await publisher.close()


if __name__ == "__main__":
    asyncio.run(main())
