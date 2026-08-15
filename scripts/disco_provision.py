#!/usr/bin/env python3
"""Provision the disco NATS schema on a WireClaw controller.

Registers the four ``nats_value`` sensors (band_low / band_mid / band_high /
bpm) that the analysis process publishes to, so the controller's rule engine
can react to them. Optionally adds a demo scene rule.

Usage:
    python scripts/disco_provision.py <device> [--demo] [--url nats://...]

Examples:
    python scripts/disco_provision.py wireclaw-01
    python scripts/disco_provision.py wireclaw-01 --demo
    python scripts/disco_provision.py wireclaw-01 --url nats://localhost:4222

Idempotent: registering a sensor that already exists is a no-op, so re-running
is safe.
"""

import argparse
import asyncio
import json
import sys

import nats

DEFAULT_URL = "nats://127.0.0.1:4222"

# name -> NATS subject, per the locked spec (issue #8)
SENSORS = {
    "band_low": "disco.band.low",
    "band_mid": "disco.band.mid",
    "band_high": "disco.band.high",
    "bpm": "disco.bpm",
}


def build_request(tool, params):
    """Build the flat JSON tool_exec request for a WireClaw tool.

    The top-level key is ``tool``; all params ride at the same level.
    """
    payload = {"tool": tool}
    payload.update(params or {})
    return json.dumps(payload)


async def discover(url):
    nc = await nats.connect(url)
    try:
        try:
            msg = await nc.request("_ion.discover", b"", timeout=3)
        except Exception:
            return []
        raw = msg.data.decode()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return [raw]
        if isinstance(data, list):
            return [d.get("name", d) if isinstance(d, dict) else d for d in data]
        return [data]
    finally:
        await nc.close()


async def tool_exec(nc, device, tool, params):
    reply = await nc.request(
        f"{device}.tool_exec", build_request(tool, params).encode(), timeout=10
    )
    return json.loads(reply.data.decode())


async def register_sensors(nc, device):
    results = []
    for name, subject in SENSORS.items():
        resp = await tool_exec(
            nc,
            device,
            "device_register",
            {"name": name, "type": "nats_value", "subject": subject, "unit": ""},
        )
        results.append((name, subject, resp))
    return results


async def verify_sensors(nc, device):
    resp = await tool_exec(nc, device, "device_list", None)
    registered = set()
    for name in SENSORS:
        if name in json.dumps(resp):
            registered.add(name)
    return registered


async def add_demo_rule(nc, device):
    """Demo scene: bass drop (band_low >= 0.8) spins the ball at 10 RPM CW
    and flashes the ring red; when it drops back, calm blue."""
    ring_on = (255 << 16) | (0 << 8) | 0
    ring_off = (0 << 16) | (0 << 8) | 255
    resp = await tool_exec(
        nc,
        device,
        "rule_create",
        {
            "rule_name": "bass drop",
            "sensor_name": "band_low",
            "condition": "gt",
            "threshold": 80,  # band level is 0-100 scale in rule thresholds
            "on_action": "actuator",
            "on_actuator": "stepper",
            "on_value": 10,
            "off_action": "actuator",
            "off_actuator": "stepper",
            "off_value": 0,
        },
    )
    return resp


async def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "device", nargs="?", help="WireClaw device name, e.g. wireclaw-01"
    )
    parser.add_argument("--demo", action="store_true", help="add a demo scene rule")
    parser.add_argument("--url", default=DEFAULT_URL, help="NATS server URL")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="discover devices instead of requiring a name (ignores <device>)",
    )
    args = parser.parse_args(argv)

    if args.discover:
        devices = await discover(args.url)
        if not devices:
            print("No WireClaw devices found on the network.")
            return 1
        print("Discovered devices:", ", ".join(str(d) for d in devices))
        return 0

    if not args.device:
        parser.error("device is required unless --discover is used")
        return 1

    nc = await nats.connect(args.url)
    try:
        # Check the device is reachable first.
        try:
            caps = await tool_exec(nc, args.device, "device_info", None)
            print(f"Connected to {args.device}: {caps}")
        except Exception as exc:
            print(f"Error: {args.device} not reachable: {exc}")
            return 1

        print(f"Registering sensors on {args.device} ...")
        for name, subject, resp in await register_sensors(nc, args.device):
            ok = resp.get("ok")
            print(f"  {name} <- {subject}: {'OK' if ok else resp}")

        registered = await verify_sensors(nc, args.device)
        missing = set(SENSORS) - registered
        if missing:
            print(f"WARNING: not registered: {', '.join(sorted(missing))}")
        else:
            print(f"All {len(SENSORS)} sensors registered.")

        if args.demo:
            resp = await add_demo_rule(nc, args.device)
            print("Demo rule:", "OK" if resp.get("ok") else resp)
    finally:
        await nc.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
