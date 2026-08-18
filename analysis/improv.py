import asyncio
import json
import os
import shutil

from analysis.scenes import render_scene


class OpenClawPicker:
    """Scene picker backed by the OpenClaw LLM.

    Asks OpenClaw (via `openclaw agent --local --json`) to choose a scene for a
    musical event, then maps the reply back to a Scene from the palette. Falls
    back to the first palette scene if the reply is unparseable or names an
    unknown scene, so a flaky LLM never stalls the show.
    """

    def __init__(self, palette, runner=None):
        self._palette = palette
        self._by_name = {s.name: s for s in palette}
        self._runner = runner or _SubprocessRunner()

    async def pick(self, event_type):
        prompt = (
            "You are the improviser for a disco ball light show. A musical "
            f"event just happened: '{event_type}'. Choose one scene from this "
            f"palette: {', '.join(self._by_name)}. Reply with ONLY a JSON "
            'object like {"scene": "<name>"}.'
        )
        reply = await self._runner.run(
            ["openclaw", "agent", "--local", "--json", "--agent", "main"], prompt
        )
        name = self._extract_scene(reply)
        return self._by_name.get(name) or self._palette[0]

    @staticmethod
    def _extract_scene(reply):
        """Pull the scene name out of OpenClaw's reply envelope.

        OpenClaw returns a JSON envelope {"payloads":[{"text":...}]} and the
        model often wraps its answer in markdown code fences. Extract the text,
        strip the fences, then parse the inner JSON.
        """
        text = reply
        try:
            data = json.loads(reply)
            payloads = data.get("payloads")
            if isinstance(payloads, list) and payloads:
                text = payloads[0].get("text", reply)
        except (ValueError, AttributeError):
            pass
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            return json.loads(text).get("scene")
        except (ValueError, AttributeError):
            return None


class _SubprocessRunner:
    async def run(self, args, prompt):
        # On Windows, `openclaw` is a .cmd shim that create_subprocess_exec
        # can't launch directly; resolve it to the real executable first.
        exe = args[0]
        if os.name == "nt" and not exe.lower().endswith(".exe"):
            resolved = shutil.which(exe)
            if resolved and resolved.lower().endswith(".cmd"):
                exe = resolved
        proc = await asyncio.create_subprocess_exec(
            exe,
            *args[1:],
            "-m",
            prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        out, _ = await proc.communicate()
        return out.decode(errors="replace")


class ImprovAgent:
    """The OpenClaw improvisation layer.

    Subscribes to disco.event and, on each musical event, asks the scene picker
    (the LLM) to choose a scene, then applies it to the controller via
    tool_exec. The picker is injected so the orchestration is testable and the
    LLM backend is swappable. This is what makes the show differ every run.
    """

    def __init__(self, nc, device, picker):
        self._nc = nc
        self._device = device
        self._picker = picker

    async def start(self):
        await self._nc.subscribe("disco.event", cb=self._on_event)

    async def _on_event(self, msg):
        try:
            payload = json.loads(msg.data.decode())
        except (ValueError, UnicodeDecodeError):
            return
        event_type = payload.get("type")
        if not event_type:
            return
        try:
            scene = await self._picker.pick(event_type)
            for call in render_scene(scene):
                params = {k: v for k, v in call.items() if k != "tool"}
                payload = json.dumps({"tool": call["tool"], **params}).encode()
                await self._nc.request(f"{self._device}.tool_exec", payload, timeout=10)
        except Exception:
            # A device hiccup (e.g. briefly offline -> NoRespondersError) must
            # not kill the subscription's message loop. Log and move on.
            import logging

            logging.getLogger("improv").exception("failed to apply scene")
