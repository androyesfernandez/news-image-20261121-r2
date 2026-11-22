#!/usr/bin/env python3
"""Entry program for the news-image-20261121 round-2 poster.

The repository ships the finished poster as entry.png, drawn by the
build script in draw.py. When the grader runs this program it delivers
that poster to the output folder: the folder named by the
MAKEFUN_OUTPUT_DIR environment variable when it is set, and /output
otherwise.

Before anything is written, the program confirms the file really is
the poster this entry promises: a PNG whose header reports exactly
1024 by 1024 pixels. The payload is then written out and its size
compared against the original, so a truncated delivery is reported
instead of silently accepted.
"""

import os
import struct
import sys
from pathlib import Path

EXPECTED_SIZE = (1024, 1024)
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def poster_file():
    return Path(__file__).resolve().parent / "entry.png"


def deliver():
    poster = poster_file()
    data = poster.read_bytes()
    if data[:8] != PNG_MAGIC:
        raise SystemExit("entry.png: missing PNG signature")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != EXPECTED_SIZE:
        raise SystemExit(
            "entry.png: expected %dx%d, found %dx%d"
            % (EXPECTED_SIZE[0], EXPECTED_SIZE[1], width, height))
    # An empty variable counts as unset: fall back to /output.
    target_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / "entry.png"
    target.write_bytes(data)
    if target.stat().st_size != len(data):
        raise SystemExit("entry.png: short write to %s" % target)
    return 0


if __name__ == "__main__":
    sys.exit(deliver())
