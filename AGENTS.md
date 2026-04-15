# AGENTS

## Repo shape (source of truth)
- Python package is `papouch/` (sync API in `papouch/quido.py`, async USB API in `papouch/quido_async.py`).
- ROS package is `papouch_ros/` (catkin package; service in `papouch_ros/srv/WriteIO.srv`, nodes in `papouch_ros/scripts/`).
- CLI entrypoints are defined in `pyproject.toml` under `[project.scripts]`: `quido-cli`, `quido-list`, `quido-test`, `quido-async-test`.

## Environment and install
- Build backend is Hatchling (`pyproject.toml`); use editable install for local dev: `python -m pip install -e .`.
- Runtime deps declared in `pyproject.toml`: `pyserial`, `pyserial-asyncio`, `requests`.
- `quido-async-test` requires `serial_asyncio` (provided by `pyserial-asyncio`).

## Verified commands
- CLI help works from source: `python -m papouch.scripts.cli --help`.
- Preferred device tools after install: `quido-cli`, `quido-list`, `quido-test`, `quido-async-test`.
- ROS package is built with catkin (see `papouch_ros/CMakeLists.txt`); run ROS nodes via `rosrun papouch_ros quido_node ...` after workspace build and `source`.

## Hardware and ROS quirks
- Udev rule at `udev/20-papouch.rules` creates `/dev/ttyUSB_Quido`; prefer stable symlink paths in examples/scripts.
- In ROS `quido_node`, valid connection args are `--usb` or `--eth` (not `--dev`).

## Known gotchas
- README command examples are partly stale vs code (`--con` typo and ROS `--dev` example).
- TCP defaults are aligned to `1001` in both library and script options; preserve this unless there is a protocol-level reason to change it.
- No configured automated lint/typecheck/unit-test/CI in this repo; `quido-test` scripts are hardware smoke tools.

## Code style and documentation
- Keep changes idiomatic Python and aligned with surrounding file style; do not reformat unrelated code.
- Preserve current API behavior patterns:
  - `papouch/quido.py` and `papouch/quido_async.py` often return `True/False/None` for command outcomes instead of raising for every failure.
  - Protocol handling is byte-oriented (`as_bytes`, `*B...` framing); keep new command code consistent.
- Keep public-facing additions documented:
  - Add or update docstrings for new public classes/functions.
  - If CLI behavior changes, update `README.md` command examples in the same change.
- Prefer type hints where files already use them (notably `papouch/quido_async.py`); avoid large annotation rewrites in legacy files.
- Follow existing logging pattern (`logging.getLogger(...)` with debug/info/error).
- For `papouch_ros/scripts/`, keep ROS1/catkin compatibility conventions intact (Python shebang and ROS argument style).
