#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import argparse
import sys
from itertools import dropwhile

import bpy

argv = list(dropwhile(lambda x: x != "--", sys.argv))
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input")
parser.add_argument("-o", "--output")
args = parser.parse_args(argv[1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.preferences.addon_enable(module="io_nfs4_import")
bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
bpy.ops.import_scene.nfs4trk(
    directory=args.input,
    import_shading=True,
    import_collision=True,
    mode="GLTF",
    import_cameras=True,
)
bpy.ops.export_scene.gltf(
    filepath=args.output,
    export_attributes=True,
    export_cameras=True,
    export_extras=True,
    export_lights=True,
)
