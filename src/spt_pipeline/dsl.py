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


@dataclass
class Track2GLTF:
    destination: str = "{_temp}/{_filename}/{_filename.glb}"


@dataclass
class GodotPostprocess:
    script: str


@dataclass
class Foreach:
    actions: list[Track2GLTF | GodotPostprocess]


@dataclass
class Root(JSONWizard):
    class Meta(JSONWizard.Meta):
        tag_key = "action"
        auto_assign_tags = True

    # pipelines: list[Pipeline]
    pipelines: list[GetFiles | Foreach | Track2GLTF]
