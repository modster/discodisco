import argparse
import asyncio

import nats

from analysis.capture import Capture
from analysis.pipeline import Pipeline
from analysis.publisher import Publisher
from analysis.scenerunner import SceneRunner
from analysis.scenes import SEED_PALETTE


async def main():
    parser = argparse.ArgumentParser(
        description="Disco ball analysis + scene controller"
    )
    parser.add_argument(
        "--device",
        default=None,
        help="WireClaw device name (e.g. wireclaw-01). If set, also runs the "
        "scene controller, applying scenes on disco.event.",
    )
    parser.add_argument(
        "--url", default="nats://127.0.0.1:4222", help="NATS server URL"
    )
    args = parser.parse_args()

    publisher = Publisher(url=args.url)
    await publisher.connect()
    pipeline = Pipeline(publisher=publisher)
    capture = Capture(pipeline)

    # Optional scene controller: swap scenes on disco.event via the device.
    scene_task = None
    nc = None
    if args.device:
        nc = await nats.connect(args.url)
        runner = SceneRunner(nc, device=args.device, palette=SEED_PALETTE)
        await runner.start()
        scene_task = asyncio.create_task(_keep_running())

    try:
        await capture.run()
    finally:
        await publisher.close()
        if nc:
            await nc.close()


async def _keep_running():
    # The scene runner's subscription stays alive for the process lifetime.
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
