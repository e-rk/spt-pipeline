#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import argparse
import sys
import traceback
from itertools import dropwhile

import addon_utils
import bpy


def enable_addon(module: str) -> None:
    _, loaded = addon_utils.check(module)
    if not loaded:
        bpy.ops.preferences.addon_enable(module=module)


try:
    argv = list(dropwhile(lambda x: x != "--", sys.argv))
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument("-n", "--night", action="store_true")
    parser.add_argument("-w", "--weather", action="store_true")
    args = parser.parse_args(argv[1:])
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    enable_addon("bl_ext.user_default.speedtools")
    enable_addon("io_scene_gltf2")
    bpy.ops.import_scene.nfs4trk(
        directory=args.input,
        import_shading=True,
        import_collision=True,
        import_cameras=True,
        import_ambient=True,
        import_audio=True,
        night=args.night,
        weather=args.weather,
    )
    bpy.ops.export_scene.gltf(
        filepath=args.output,
        export_attributes=True,
        export_cameras=True,
        export_extras=True,
        export_lights=True,
        export_all_vertex_colors=False,
        export_active_vertex_color_when_no_material=False,
        export_unused_images=True,
        export_apply=True,
    )
except BaseException:
    traceback.print_exc()
    exit(1)
