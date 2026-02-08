#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager, chdir, suppress
from functools import singledispatchmethod
from pathlib import Path
import sys

from spt_pipeline.dsl import (
    Car2GLTF,
    Foreach,
    GetFiles,
    GodotPostprocess,
    GodotRun,
    Track2GLTF,
)
from spt_pipeline.utils import RESOURCE_DIR, run_blender, run_godot

logger = logging.getLogger(__name__)


class PipelineProcessor(AbstractContextManager):
    def __init__(self, source, destination, path=None, paths: dict[str, Path] = {}, executor=None):
        self.source = source
        self.destination = destination
        self.path = path
        self.paths: dict[str, Path] = paths
        max_workers = 1 if sys.platform == "win32" else 6
        self.executor = executor if executor else ThreadPoolExecutor(max_workers=max_workers)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _with_ctx(self, action, **kwargs):
        path = kwargs.get("path", None)
        with PipelineProcessor(
            source=self.source,
            destination=self.destination,
            path=path,
            paths=self.paths,
            executor=self.executor,
        ) as local:
            return local.run_action(action)

    def format(self, string) -> str:
        filename = self.path.name.lower() if isinstance(self.path, Path) else None
        f = {
            "_source": self.source,
            "_destination": self.destination,
            "_filename": filename,
            "_path": self.path,
        }
        return string.format(**f)

    def format_path(self, string) -> Path:
        return Path(self.format(string))

    def spawn_blender(self, args):
        try:
            run_blender(args, self.paths)
            return True
        except subprocess.CalledProcessError:
            return False

    @singledispatchmethod
    def run_action(self, action) -> str:
        raise NotImplementedError(f"Action {action} not implemented")

    @run_action.register
    def _(self, action: Track2GLTF):
        logger.debug(action)
        destination = self.format_path(action.destination)
        logger.info(f"Converting track {self.path} into {destination}")
        with suppress(FileExistsError):
            os.makedirs(destination.parent)
        args = [
            "--background",
            "--python",
            RESOURCE_DIR / "track2gltf.py",
            "--",
            "--input",
            self.path,
            "--output",
            destination,
        ]
        if action.night:
            args.append("--night")
        if action.weather:
            args.append("--weather")
        if self.spawn_blender(args):
            logger.info(f"Successfuly converted {self.path}")
        else:
            logger.error(f"Failed to convert {self.path}")

    @run_action.register
    def _(self, action: Car2GLTF):
        logger.debug(action)
        destination = self.format_path(action.destination)
        logger.info(f"Converting car {self.path} into {destination}")
        with suppress(FileExistsError):
            os.makedirs(destination.parent)
        args = [
            "--background",
            "--python",
            RESOURCE_DIR / "car2gltf.py",
            "--",
            "--input",
            self.path,
            "--output",
            destination,
        ]
        if self.spawn_blender(args):
            logger.info(f"Successfuly converted {self.path}")
        else:
            logger.error(f"Failed to convert {self.path}")

    @run_action.register
    def _(self, action: Foreach):
        logger.debug(action)
        return list(
            self.executor.map(lambda x: self.run_actions_int(action.actions, path=x), self.path)
        )

    @run_action.register
    def _(self, action: GetFiles):
        logger.debug(f"{action} p={self.path}")
        match = self.format(action.match)
        directory = self.format(action.directory)
        files = list({p.parent for p in Path(directory).rglob(match, case_sensitive=False)})
        if action.required and not files:
            raise FileNotFoundError(f"No files found in {directory}")
        elif not files:
            logger.warning(f"No files found in {directory}")
        return files

    @run_action.register
    def _(self, action: GodotPostprocess):
        logger.debug(action)

    @run_action.register
    def _(self, action: GodotRun):
        directory = self.format(action.workdir)
        with chdir(directory):
            run_godot(action.args, self.paths)

    def run_actions_int(self, actions, path):
        for action in actions:
            path = self._with_ctx(action, path=path)

    def run_actions(self, actions):
        self.run_actions_int(actions, self.path)
