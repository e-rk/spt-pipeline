#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import logging
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager, suppress
from functools import singledispatchmethod
from pathlib import Path

from spt_pipeline.dsl import Foreach, GetFiles, GodotPostprocess, Track2GLTF

logger = logging.getLogger(__name__)


class PipelineProcessor(AbstractContextManager):
    def __init__(self, source, destination, path=None, executor=None):
        self.source = source
        self.destination = destination
        self.path = path
        self.executor = executor if executor else ThreadPoolExecutor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _with_ctx(self, action, **kwargs):
        path = kwargs.get("path", None)
        with PipelineProcessor(
            source=self.source, destination=self.destination, path=path, executor=self.executor
        ) as local:
            return local.run_action(action)

    def format(self, string) -> str:
        filename = self.path.name if self.path else None
        f = {
            "_source": self.source,
            "_destination": self.destination,
            "_filename": filename,
            "_path": self.path,
        }
        return string.format(**f)

    def format_path(self, string) -> Path:
        return Path(self.format(string))

    @staticmethod
    def spawn(args):
        subprocess.run(args, check=True, capture_output=True)

    @singledispatchmethod
    def run_action(self, action) -> str:
        raise NotImplementedError(f"Action {action} not implemented")

    @run_action.register
    def _(self, action: Track2GLTF):
        logger.debug(action)
        destination = self.format_path(action.destination)
        with suppress(FileExistsError):
            os.makedirs(destination.parent)
        self.spawn(
            [
                "blender",
                "--background",
                "--python",
                "./src/resources/track2gltf.py",
                "--",
                "--input",
                self.path,
                "--output",
                destination,
            ]
        )

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
        return list(Path(directory).glob(match))

    @run_action.register
    def _(self, action: GodotPostprocess):
        logger.debug(action)

    def run_actions_int(self, actions, path):
        for action in actions:
            path = self._with_ctx(action, path=path)

    def run_actions(self, actions):
        self.run_actions_int(actions, self.path)
