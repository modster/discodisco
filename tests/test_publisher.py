import asyncio

import pytest

from analysis.publisher import Publisher


@pytest.mark.asyncio
async def test_publishes_band_levels():
    p = Publisher(url="nats://127.0.0.1:4222")
    await p.connect()
    subs = {
        subject: await p._nc.subscribe(subject)
        for subject in ("disco.band.low", "disco.band.mid", "disco.band.high")
    }
    await p.publish_bands({"low": 0.5, "mid": 0.3, "high": 0.1})
    received = {}
    for subject, sub in subs.items():
        msg = await sub.next_msg(timeout=2)
        received[subject] = msg.data.decode()
    await p.close()
    assert received["disco.band.low"] == "0.5"
    assert received["disco.band.mid"] == "0.3"
    assert received["disco.band.high"] == "0.1"


@pytest.mark.asyncio
async def test_publishes_bpm():
    p = Publisher(url="nats://127.0.0.1:4222")
    await p.connect()
    sub = await p._nc.subscribe("disco.bpm")
    await p.publish_bpm(128.0)
    msg = await sub.next_msg(timeout=2)
    await p.close()
    assert msg.data.decode() == "128.0"


@pytest.mark.asyncio
async def test_publishes_beat_event():
    p = Publisher(url="nats://127.0.0.1:4222")
    await p.connect()
    sub = await p._nc.subscribe("disco.beat")
    await p.publish_beat(ts=1000, bpm=120.0)
    msg = await sub.next_msg(timeout=2)
    await p.close()
    import json

    assert json.loads(msg.data) == {"ts": 1000, "bpm": 120.0}


@pytest.mark.asyncio
async def test_publishes_musical_event():
    p = Publisher(url="nats://127.0.0.1:4222")
    await p.connect()
    sub = await p._nc.subscribe("disco.event")
    await p.publish_event("song_change", ts=2000)
    msg = await sub.next_msg(timeout=2)
    await p.close()
    import json

    assert json.loads(msg.data) == {"type": "song_change", "ts": 2000}
