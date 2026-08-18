import argparse
import asyncio

import nats

from analysis.capture import Capture
from analysis.commands import CommandController
from analysis.improv import ImprovAgent, OpenClawPicker
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
        "--improv",
        action="store_true",
        help="Use the OpenClaw LLM to improvise scenes (instead of the "
        "deterministic scene runner).",
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
    nc = None
    if args.device:
        nc = await nats.connect(args.url)
        if args.improv:
            picker = OpenClawPicker(palette=SEED_PALETTE)
            agent = ImprovAgent(nc, device=args.device, picker=picker)
            await agent.start()
        else:
            runner = SceneRunner(nc, device=args.device, palette=SEED_PALETTE)
            await runner.start()
        # Reserved human commands (stop/off/calm/wild) via disco.command.
        commands = CommandController(client=_NatsClient(nc), device=args.device)
        await nc.subscribe("disco.command", cb=commands.handle)

    try:
        await capture.run()
    finally:
        await publisher.close()
        if nc:
            await nc.close()


class _NatsClient:
    """Adapter so CommandController can issue tool_exec over NATS."""

    def __init__(self, nc):
        self._nc = nc

    async def tool_exec(self, device, tool, params):
        import json

        payload = json.dumps({"tool": tool, **params}).encode()
        await self._nc.request(f"{device}.tool_exec", payload, timeout=10)


async def _keep_running():
    # The scene runner's subscription stays alive for the process lifetime.
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
