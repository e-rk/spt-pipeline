#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

from dataclasses import dataclass
from typing import Union

from dataclass_wizard import JSONWizard


@dataclass
class GetFiles:
    match: str
    directory: str
    dir_only: bool = False
    required: bool = False
    recursive: bool = False


@dataclass
class Track2GLTF:
    destination: str = "{_temp}/{_filename}/{_filename.glb}"
    night: bool = False
    weather: bool = False


@dataclass
class Car2GLTF:
    destination: str = "{_temp}/{_filename}/{_filename.glb}"


@dataclass
class Heli2GLTF:
    destination: str = "{_temp}/{_filename}/{_filename.glb}"


@dataclass
class FshUnpack:
    files: list[str]
    destination: str


@dataclass
class GodotPostprocess:
    script: str


@dataclass
class GodotRun:
    workdir: str
    args: list[str]


DslTypes = Union[
    GetFiles,
    Track2GLTF,
    Car2GLTF,
    Heli2GLTF,
    FshUnpack,
    GodotPostprocess,
    GodotRun,
]


@dataclass
class Foreach:
    actions: list[Union[DslTypes, "Foreach"]]


@dataclass
class Root(JSONWizard):
    class Meta(JSONWizard.Meta):
        tag_key = "action"
        auto_assign_tags = True

    # pipelines: list[Pipeline]
    pipelines: list[Union[DslTypes, Foreach]]
