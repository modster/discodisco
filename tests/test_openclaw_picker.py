import asyncio

from analysis.improv import OpenClawPicker
from analysis.scenes import SEED_PALETTE


class FakeRunner:
    def __init__(self, reply):
        self.reply = reply

    async def run(self, args, prompt):
        return self.reply


def _envelope(text):
    import json

    return json.dumps({"payloads": [{"text": text, "mediaUrl": None}], "meta": {}})


def test_picker_parses_openclaw_envelope():
    # OpenClaw wraps the reply in a JSON envelope + markdown fences.
    reply = _envelope('```json\n{"scene": "rage"}\n```')
    picker = OpenClawPicker(palette=SEED_PALETTE, runner=FakeRunner(reply))
    scene = asyncio.run(picker.pick("drop"))
    assert scene.name == "rage"


def test_picker_parses_plain_json_text():
    reply = _envelope('{"scene": "calm"}')
    picker = OpenClawPicker(palette=SEED_PALETTE, runner=FakeRunner(reply))
    scene = asyncio.run(picker.pick("silence"))
    assert scene.name == "calm"


def test_picker_falls_back_on_unknown_scene():
    reply = _envelope('```json\n{"scene": "nonexistent"}\n```')
    picker = OpenClawPicker(palette=SEED_PALETTE, runner=FakeRunner(reply))
    scene = asyncio.run(picker.pick("drop"))
    assert scene.name == SEED_PALETTE[0].name


def test_picker_falls_back_on_bad_reply():
    picker = OpenClawPicker(palette=SEED_PALETTE, runner=FakeRunner("garbage"))
    scene = asyncio.run(picker.pick("drop"))
    assert scene.name == SEED_PALETTE[0].name
