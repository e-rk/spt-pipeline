#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import logging
import os
import subprocess
from sys import version
import time
from pathlib import Path
from typing import TextIO

import click
from yaml import safe_load

from spt_pipeline.dsl import Root
from spt_pipeline.processor import PipelineProcessor
from spt_pipeline.utils import run_process, get_manifest, format_paths, run_winget

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)


@click.command()
@click.option("--source", "-s", type=click.Path(path_type=Path))
@click.option("--destination", "-d", type=click.Path(path_type=Path))
@click.option("--blender", "-b", type=click.Path(path_type=Path))
@click.option("--ffmpeg", "-f", type=click.Path(path_type=Path))
@click.argument("file", type=click.File())
def run(source: Path, destination: Path, blender: Path, ffmpeg: Path, file: TextIO) -> None:
    manifest = get_manifest()
    paths = format_paths(manifest)

    if blender:
        paths["blender"] = blender

    if ffmpeg:
        paths["ffmpeg"] = ffmpeg

    main(source=source, file=file, paths=paths)


def install_addon(blender: Path, addon_path: Path):
    logger.info(f"Installing addon {addon_path}")
    try:
        run_process(
            [
                blender,
                "--command",
                "extension",
                "install-file",
                "-e",
                "-r",
                "user_default",
                addon_path,
            ]
        )
        time.sleep(3)  # Apparently needed for Blender to finish installation
        logger.info("Addon installed successfuly")
    except subprocess.CalledProcessError as e:
        logger.error("Addon installation failed")
        stdout = e.stdout.decode("utf-8")
        if stdout:
            logger.error(stdout)
        stderr = e.stderr.decode("utf-8")
        if stderr:
            logger.error(stderr)
        raise


def install_blender():
    run_winget(id="BlenderFoundation.Blender", version="5.0.1")


def main(
    source: Path,
    file: TextIO,
    paths: dict[str, Path],
    blender_install: bool = False,
) -> None:
    logger.info("Installation started")
    manifest = get_manifest()
    paths = format_paths(manifest)
    destination = Path(".")
    try:
        if blender_install:
            install_blender()

        install_addon(blender=paths["blender"], addon_path=paths["speedtools"])

        data = safe_load(file)
        config = Root.from_dict(data)
        logger.debug(config)
        processor = PipelineProcessor(source=source, destination=destination, paths=paths)
        processor.run_actions(config.pipelines)
        logger.info("Success. You can now close the window.")
    except Exception as ex:
        logger.error("Import failed")
        logger.exception(ex)
        raise
    finally:
        logger.debug("Clearing temporary files")
