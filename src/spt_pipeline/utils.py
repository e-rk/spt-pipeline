import os
import subprocess
import sys
from pathlib import Path
import json

RESOURCE_DIR = Path(__file__).parent / "resources"
ADDON_URL = "https://github.com/e-rk/speedtools/releases/download/v{speedtools}/speedtools-{speedtools}.zip"

SPEEDTOOLS_PATH = "speedtools-{speedtools}.zip"

if os.name == "nt":
    GODOT_EXE = "Godot_v{godot}-stable_win64.exe"
    BLENDER_PATH = "C:\\Program Files\\Blender Foundation\\Blender 5.0\\blender.exe"
else:
    GODOT_EXE = "Godot_v{godot}-stable_linux.x86_64"
    BLENDER_PATH = "blender"

DEFAULT_MANIFEST = {
    "speedtools": "0.26.0",
    "blender": "5.0.1",
    "godot": "4.6",
}


def run_process(args: list) -> subprocess.CompletedProcess[bytes]:
    if sys.platform == "linux":
        env = dict(os.environ)  # make a copy of the environment
        lp_key = "LD_LIBRARY_PATH"  # for GNU/Linux and *BSD.
        lp_orig = env.get(lp_key + "_ORIG")
        if lp_orig is not None:
            env[lp_key] = lp_orig  # restore the original, unmodified value
        else:
            # This happens when LD_LIBRARY_PATH was not set.
            # Remove the env var as a last resort:
            env.pop(lp_key, None)
        return subprocess.run(args, check=True, capture_output=True, env=env)  # create the process
    else:
        return subprocess.run(args, check=True, capture_output=True)


def format_paths(manifest: dict[str, str]) -> dict[str, Path]:
    print(manifest)
    return {
        "godot": Path(GODOT_EXE.format(**manifest)),
        "blender": Path(BLENDER_PATH.format(**manifest)),
        "speedtools": Path("bundle") / SPEEDTOOLS_PATH.format(**manifest),
    }


def get_manifest() -> dict[str, str]:
    try:
        with open("manifest.json", "r") as f:
            return dict(json.load(f))
    except FileNotFoundError:
        return DEFAULT_MANIFEST
