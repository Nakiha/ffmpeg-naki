"""
NakiFFmpeg - Video Stream Parser
"""

from pathlib import Path
from typing import List, Optional
import ctypes
import os
import sys

__version__ = "1.0.0"

CODEC_H264 = 0
CODEC_HEVC = 1
CODEC_VVC = 2
CODEC_AV1 = 3
CODEC_VP9 = 4


class NalUnit:
    """NAL unit"""
    def __init__(self, type: int, size: int, offset: int):
        self.type = type
        self.size = size
        self.offset = offset

    def __repr__(self):
        return f"NalUnit(type={self.type}, size={self.size})"


def _find_dll() -> Path:
    pkg = Path(__file__).parent / "naki_parser.dll"
    if pkg.exists():
        return pkg
    build = Path(__file__).parent.parent / "build" / "bin" / "naki_parser.dll"
    if build.exists():
        return build
    raise RuntimeError(
        "naki_parser.dll not found.\n"
        "Build: cmake -B build && cmake --build build"
    )


_lib = None


def _get_lib():
    global _lib
    if _lib is None:
        dll = _find_dll()
        if sys.platform == "win32":
            os.add_dll_directory(str(dll.parent))
        _lib = ctypes.CDLL(str(dll))
        _lib.naki_parser_version.restype = ctypes.c_char_p
    return _lib


def version() -> str:
    return _get_lib().naki_parser_version().decode()


def parse_h264(data: bytes) -> List[NalUnit]:
    """Parse H.264 Annex B data"""
    nals = []
    sc = b"\x00\x00\x00\x01"
    sc3 = b"\x00\x00\x01"
    pos = 0

    while pos < len(data):
        i4 = data.find(sc, pos)
        i3 = data.find(sc3, pos)
        if i4 < 0 and i3 < 0:
            break
        start = i4 if i4 >= 0 and (i3 < 0 or i4 <= i3) else i3
        sc_len = 4 if start == i4 else 3
        nal_pos = start + sc_len

        n4 = data.find(sc, nal_pos)
        n3 = data.find(sc3, nal_pos)
        next_pos = min([x for x in [n4, n3] if x >= 0], default=len(data))

        nal_size = next_pos - nal_pos
        if nal_size > 0:
            nal_type = data[nal_pos] & 0x1F
            nals.append(NalUnit(nal_type, nal_size, start))

        pos = next_pos

    return nals


__all__ = ["version", "parse_h264", "NalUnit", "CODEC_H264", "CODEC_HEVC", "CODEC_VVC"]
