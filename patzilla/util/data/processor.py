# -*- coding: utf-8 -*-
# (c) 2022 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import sys
import typing as t
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class AbstractProcessorHandler:

    @property
    def suffix(self):
        raise NotImplementedError()

    def handle(self, resource, outstream: t.IO[str]):
        raise NotImplementedError()


class Processor:
    """
    Generic engine for processing file-like data.

    Takes a single resource as input, processes its content using a given handler,
    and outputs the result either to STDOUT, or to a file within given output directory.
    """

    def __init__(self, handler: AbstractProcessorHandler, outdir: Path = None, outprefix: str = None):
        self.handler = handler
        self.outdir = outdir
        self.outprefix = outprefix

    def process(self, resource: t.Union[str, Path]):
        """
        Process one or multiple documents from single or archive file.
        """

        if Path(resource).is_dir():
            raise NotImplementedError("Processing directory with multiple files is not implemented yet")

        resource_name = Path(resource).stem
        if resource.endswith(".zip"):
            ziparchive = zipfile.ZipFile(resource)
            zipinfo: zipfile.ZipInfo
            filelist = [zipinfo.filename for zipinfo in ziparchive.filelist]
            for filename in sorted(filelist):
                nested_resource_name = f"{resource_name}_{Path(filename).stem}"
                fp = ziparchive.open(filename)
                self.process_single(fp, name=nested_resource_name)
        else:
            self.process_single(resource, name=resource_name)

    def process_single(self, resource: t.Union[str, Path, t.IO[bytes]], name: str):
        """
        Process one or multiple documents from single file or input stream.
        """

        # Write to STDOUT.
        if self.outdir is None:
            outstream = sys.stdout
            logger.info(f"Output file: STDOUT")

        # Write to file.
        else:
            if not self.outdir.is_dir():
                raise NotADirectoryError(f"Invalid output directory: {self.outdir}")

            if self.outprefix:
                name = f"{self.outprefix}{name}"
            outfile = self.outdir.joinpath(name).with_suffix(self.handler.suffix).absolute()

            logger.info(f"Output file: {outfile}")
            outstream = open(outfile, "w")

        self.handler.handle(resource, outstream)
        if outstream is not sys.stdout:
            outstream.close()
