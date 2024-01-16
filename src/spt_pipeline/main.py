#
# Copyright (c) 2024 Rafał Kuźnia <rafal.kuznia@protonmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import logging
from pathlib import Path
from typing import TextIO

import click
from dsl import Root
from processor import PipelineProcessor
from yaml import safe_load

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


@click.command()
@click.option("--source", "-s", type=click.Path(path_type=Path))
@click.option("--destination", "-d", type=click.Path(path_type=Path))
@click.argument("file", type=click.File())
def run(source: Path, destination: Path, file: TextIO) -> None:
    data = safe_load(file)
    config = Root.from_dict(data)
    logger.debug(config)
    processor = PipelineProcessor(source=source, destination=destination)
    processor.run_actions(config.pipelines)
