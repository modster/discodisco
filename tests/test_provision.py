import json

from scripts.disco_provision import build_request


def test_build_request_top_level_tool_key():
    req = json.loads(build_request("led_set", {"r": 255, "g": 0, "b": 0}))
    assert req["tool"] == "led_set"
    assert req["r"] == 255
    assert req["g"] == 0
    assert req["b"] == 0


def test_build_request_no_params():
    req = json.loads(build_request("device_list", None))
    assert req == {"tool": "device_list"}


def test_build_request_merges_params():
    req = json.loads(
        build_request("device_register", {"name": "band_low", "type": "nats_value"})
    )
    assert req["tool"] == "device_register"
    assert req["name"] == "band_low"
    assert req["type"] == "nats_value"
