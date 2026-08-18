# Task 2 Report: Python — `render_scene` emits `ring_chase`

## What I implemented

Changed `render_scene` in `analysis/scenes.py` to emit a single `ring_chase`
tool call instead of `ring_set` + `stepper_set`. The chase color comes from the
scene's low band (`_pack(scene.band_colors["low"])`) and the direction follows
the scene via `_DIR_MAP`. The comet chase is now the sole ring driver; the
per-LED `_BAND_LED_GROUPS` construction and `stepper_set` were removed.

## TDD evidence

### RED (before implementation)

```
$ .\.venv\Scripts\python -m pytest tests/test_scenes.py tests/test_improv.py -q
..FF..F..F
FAILED tests/test_scenes.py::test_render_scene_produces_ring_chase - AssertionError: assert 'ring_chase' in ['ring_set', 'stepper_set']
FAILED tests/test_scenes.py::test_render_scene_ring_chase_has_color_and_dir - StopIteration
FAILED tests/test_improv.py::test_agent_applies_picked_scene_on_event - AssertionError: assert 'ring_chase' in {'ring_set', 'stepper_set'}
FAILED tests/test_improv.py::test_agent_survives_device_offline - AssertionError: assert 'ring_chase' in ['ring_set', 'stepper_set']
4 failed, 6 passed
```

### GREEN (after implementation)

```
$ .\.venv\Scripts\python -m pytest -q
55 passed in 0.60s
```

## Files changed

- `analysis/scenes.py` — `render_scene` now returns
  `[{"tool":"ring_chase","color":...,"dir":...}]`.
- `tests/test_scenes.py` — replaced the two obsolete `ring_set`/`stepper_set`
  tests with `test_render_scene_produces_ring_chase` and
  `test_render_scene_ring_chase_has_color_and_dir` (also removed the two other
  obsolete `ring_set`/`stepper_set` tests in the same file).
- `tests/test_improv.py` — updated ring assertions to `ring_chase` (2 tests).
- `tests/test_commands.py` — updated `calm`/`wild` scene assertions to
  `ring_chase` (2 tests).
- `tests/test_scene_controller.py` — updated scene-application assertion (1
  test).
- `tests/test_scenerunner.py` — updated scene-application assertion (1 test).

## Self-review findings

- The brief only listed `test_scenes.py` and `test_improv.py`, but the full
  suite (`pytest -q`) surfaced 4 more tests in `test_commands.py`,
  `test_scene_controller.py`, and `test_scenerunner.py` that asserted
  `ring_set`/`stepper_set` on scene application. I updated those too so the
  whole suite stays green, per the task's "run the full Python suite, all must
  pass" requirement.
- The `off` reserved command still uses `ring_set` with `(r,g,b)` params — that
  is a separate reserved-command concern (turning everything off), not scene
  rendering, so I left it untouched. Its test still passes.
- `render_scene` keeps `rpm = scene.bpm_endpoints["fast_rpm"]` per the brief's
  exact replacement code, but that variable is now unused (no `stepper_set`).
  Minor dead code; kept to match the brief verbatim.

## Issues / concerns

- Unused `rpm` variable in `render_scene` (matches brief verbatim; could be
  dropped in a follow-up).
- The brief's commit command listed only 3 files; I committed 6 because the
  extra 3 test files were required to keep the full suite passing.

## Commit

`1de76af` feat(analysis): render_scene emits ring_chase instead of stepper_set
