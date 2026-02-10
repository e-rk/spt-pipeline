#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import argparse
import sys
from itertools import dropwhile

import bpy

try:
    argv = list(dropwhile(lambda x: x != "--", sys.argv))
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    args = parser.parse_args(argv[1:])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # bpy.ops.preferences.addon_enable(module="io_nfs4_import")
    bpy.ops.preferences.addon_enable(module="bl_ext.user_default.speedtools")
    bpy.ops.preferences.addon_enable(module="io_scene_gltf2")
    bpy.ops.import_scene.nfs4car(
        directory=args.input,
        import_lights=True,
        import_audio=True,
    )
    bpy.ops.export_scene.gltf(
        filepath=args.output,
        export_attributes=True,
        export_extras=True,
        export_lights=True,
    )
except:
    exit(1)
