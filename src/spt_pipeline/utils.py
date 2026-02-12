import os
import subprocess
import sys
from pathlib import Path
import json
import logging
from typing import Sequence, TypeVar
import errno

logger = logging.getLogger(__name__)


T = TypeVar("T")
Ty = TypeVar("Ty")


RESOURCE_DIR = Path(__file__).parent / "resources"
ADDON_URL = "https://github.com/e-rk/speedtools/releases/download/v{speedtools}/speedtools-{speedtools}.zip"

SPEEDTOOLS_PATH = "speedtools-{speedtools}.zip"

if os.name == "nt":
    GODOT_EXE = "Godot_v{godot}-stable_win64.exe"
    BLENDER_PATH = (
        Path("C:/") / "Program Files" / "Blender Foundation" / "Blender 5.0" / "blender.exe"
    )
    FFMPEG_PATH = Path()
else:
    GODOT_EXE = "Godot_v{godot}-stable_linux.x86_64"
    BLENDER_PATH = Path("blender")
    FFMPEG_PATH = Path("ffmpeg")

DEFAULT_MANIFEST = {
    "speedtools": "0.26.0",
    "blender": "5.0.1",
    "godot": "4.6",
}


def run_process(args: list, env={}) -> subprocess.CompletedProcess[bytes]:
    this_env = dict(os.environ)  # make a copy of the environment
    if sys.platform == "linux":
        lp_key = "LD_LIBRARY_PATH"  # for GNU/Linux and *BSD.
        lp_orig = this_env.get(lp_key + "_ORIG")
        if lp_orig is not None:
            this_env[lp_key] = lp_orig  # restore the original, unmodified value
        else:
            # This happens when LD_LIBRARY_PATH was not set.
            # Remove the env var as a last resort:
            this_env.pop(lp_key, None)
    run_env = this_env | env
    return subprocess.run(args, check=True, capture_output=True, env=run_env)


def format_paths(manifest: dict[str, str]) -> dict[str, Path]:
    ffmpeg_path = Path("ffmpeg")
    if os.name == "nt":
        ffmpeg_path = (
            Path("bundle")
            / "ffmpeg-{ffmpeg}-essentials_build".format(**manifest)
            / "bin"
            / "ffmpeg.exe"
        )

    return {
        "godot": Path(GODOT_EXE.format(**manifest)),
        "blender": BLENDER_PATH,
        "speedtools": Path("bundle") / SPEEDTOOLS_PATH.format(**manifest),
        "ffmpeg": ffmpeg_path,
    }


def get_manifest() -> dict[str, str]:
    try:
        with open("manifest.json", "r") as f:
            return dict(json.load(f))
    except FileNotFoundError:
        return DEFAULT_MANIFEST


def run_winget(id: str, version: str):
    if os.name != "nt":
        logger.error("Auto-installation not available on platforms other than Windows.")
        return
    try:
        logger.info(f"Installing {id}:{version}. This will take a while.")
        run_log(["winget", "install", "--silent", "-e", "--id", id, "-v", version])
        logger.info(f"{id}:{version} installation complete")
    except subprocess.CalledProcessError as e:
        logger.error(f"{id}:{version} installation failed")
        raise


def run_log(args: list, env={}):
    try:
        result = run_process(args, env)
        stdout = result.stdout.decode("utf-8")
        if stdout:
            logger.debug(stdout)
        stderr = result.stderr.decode("utf-8")
        if stderr:
            logger.debug(stderr)
    except subprocess.CalledProcessError as e:
        logger.error(f"Blender args: {args}")
        logger.error("Blender failed")
        stdout = e.stdout.decode("utf-8")
        if stdout:
            logger.error(stdout)
        stderr = e.stderr.decode("utf-8")
        if stderr:
            logger.error(stderr)
            raise


def run_blender(args: list, paths: dict[str, Path]):
    this_env = dict(os.environ)
    ffmpeg_dir = paths["ffmpeg"].parent.resolve()
    path_var = this_env["PATH"]
    new_path = f"{ffmpeg_dir}{os.pathsep}{path_var}"
    new_env = {"PATH": new_path}
    blender_exe = paths["blender"]
    run_log([blender_exe] + args, env=new_env)


def run_godot(args: list, paths: dict[str, Path]):
    godot_exe = paths["godot"]
    run_log([godot_exe] + args)


def list_startswith(a: Sequence[T], b: Sequence[Ty]) -> bool:
    if a and b:
        a1, *arest = a
        b1, *brest = b
        return a1 == b1 and list_startswith(arest, brest)
    return True


def get_path_case_insensitive(stem: Path, target: Path) -> Path:
    def recurse(target: Path) -> Path | None:
        if target == stem:
            return target
        if target.exists():
            return target
        parent = recurse(target.parent)
        if parent:
            files = {p.name.lower(): p for p in parent.glob("*")}
            return files.get(target.name.lower())
        return None

    if os.name == "nt":
        return target

    if not list_startswith(stem.parts, target.parts):
        raise ValueError("Invalid argument: stem is not a prefix of path")

    if not stem.exists():
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(target))

    file = recurse(target)
    if not file:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(target))
    return file
