"""
NakiFFmpeg - Python bindings for NAKI FFmpeg software decoder

A Python wrapper for the NAKI FFmpeg build, providing pure software
NAL analysis capabilities without conflicting with hardware-accelerated
FFmpeg installations.

Usage:
    from naki_ffmpeg import NakiDecoder

    decoder = NakiDecoder()
    decoder.open("video.mp4")
    info = decoder.get_stream_info()
"""

import ctypes
import ctypes.util
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Find the NAKI FFmpeg libraries
def _find_naki_lib() -> Path:
    """Find the NAKI FFmpeg library directory."""
    # Check common locations
    script_dir = Path(__file__).parent
    candidates = [
        script_dir / "ffmpeg-dist-naki" / "bin",
        script_dir.parent / "ffmpeg-dist-naki" / "bin",
        Path("ffmpeg-dist-naki/bin"),
    ]

    for candidate in candidates:
        if (candidate / "nakiavcodec.dll").exists():
            return candidate

    raise RuntimeError(
        "Could not find NAKI FFmpeg libraries. "
        "Please run build_naki_soft.sh first."
    )


# Library paths
_LIB_DIR: Optional[Path] = None
_LIBS: Dict[str, ctypes.CDLL] = {}


def _load_library(name: str) -> ctypes.CDLL:
    """Load a NAKI FFmpeg library."""
    global _LIB_DIR, _LIBS

    if name in _LIBS:
        return _LIBS[name]

    if _LIB_DIR is None:
        _LIB_DIR = _find_naki_lib()

    lib_path = _LIB_DIR / f"{name}.dll"
    if not lib_path.exists():
        raise RuntimeError(f"Library not found: {lib_path}")

    # Add library directory to DLL search path (Windows)
    if sys.platform == "win32":
        os.add_dll_directory(str(_LIB_DIR))

    _LIBS[name] = ctypes.CDLL(str(lib_path))
    return _LIBS[name]


# FFmpeg constant definitions
AV_CODEC_ID_H264 = 27
AV_CODEC_ID_HEVC = 173
AV_CODEC_ID_VVC = 196
AV_CODEC_ID_AV1 = 225

AV_PICTURE_TYPE_I = 1
AV_PICTURE_TYPE_P = 2
AV_PICTURE_TYPE_B = 3
AV_PICTURE_TYPE_S = 4
AV_PICTURE_TYPE_SI = 5
AV_PICTURE_TYPE_SP = 6
AV_PICTURE_TYPE_BI = 7


class AVPacket(ctypes.Structure):
    """FFmpeg AVPacket structure."""
    _fields_ = [
        ("buf", ctypes.c_void_p),
        ("pts", ctypes.c_int64),
        ("dts", ctypes.c_int64),
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_int),
        ("stream_index", ctypes.c_int),
        ("flags", ctypes.c_int),
        ("side_data", ctypes.c_void_p),
        ("side_data_elems", ctypes.c_int),
        ("duration", ctypes.c_int64),
        ("pos", ctypes.c_int64),
        ("opaque", ctypes.c_void_p),
        ("opaque_ref", ctypes.c_void_p),
        ("time_base", ctypes.c_void_p),  # AVRational
    ]


class NALUnit:
    """Represents a NAL unit in video stream."""

    def __init__(self, data: bytes, nal_type: int, offset: int):
        self.data = data
        self.nal_type = nal_type
        self.offset = offset

    @property
    def size(self) -> int:
        return len(self.data)

    def __repr__(self):
        return f"NALUnit(type={self.nal_type}, size={self.size}, offset={self.offset})"


class NALAnalyzer:
    """NAL unit analyzer for H.264/HEVC/VVC streams."""

    # H.264 NAL unit types
    H264_NAL_TYPES = {
        1: "Non-IDR Slice",
        2: "Slice Data A",
        3: "Slice Data B",
        4: "Slice Data C",
        5: "IDR Slice",
        6: "SEI",
        7: "SPS",
        8: "PPS",
        9: "AUD",
        10: "End of Sequence",
        11: "End of Stream",
        12: "Filler",
    }

    # HEVC NAL unit types
    HEVC_NAL_TYPES = {
        0: "TRAIL_N",
        1: "TRAIL_R",
        2: "TSA_N",
        3: "TSA_R",
        4: "STSA_N",
        5: "STSA_R",
        6: "RADL_N",
        7: "RADL_R",
        8: "RASL_N",
        9: "RASL_R",
        16: "BLA_W_LP",
        17: "BLA_W_RADL",
        18: "BLA_N_LP",
        19: "IDR_W_RADL",
        20: "IDR_N_LP",
        21: "CRA_NUT",
        32: "VPS",
        33: "SPS",
        34: "PPS",
        35: "AUD",
        36: "EOS_NUT",
        37: "EOB_NUT",
        38: "FD_NUT",
        39: "PREFIX_SEI",
        40: "SUFFIX_SEI",
    }

    def __init__(self):
        self._lib = None

    def _load_lib(self):
        if self._lib is None:
            self._lib = _load_library("nakiavcodec")
        return self._lib

    @staticmethod
    def find_nal_units(data: bytes, codec: str = "h264") -> List[NALUnit]:
        """
        Find all NAL units in the given data.

        Args:
            data: Raw byte data containing NAL units
            codec: Codec type ("h264", "hevc", "vvc")

        Returns:
            List of NALUnit objects
        """
        nal_units = []
        start_code = b'\x00\x00\x00\x01'
        start_code_3 = b'\x00\x00\x01'

        pos = 0
        while pos < len(data):
            # Find start code
            idx_4 = data.find(start_code, pos)
            idx_3 = data.find(start_code_3, pos)

            if idx_4 == -1 and idx_3 == -1:
                break

            # Prefer 4-byte start code if found earlier
            if idx_4 != -1 and (idx_3 == -1 or idx_4 <= idx_3):
                nal_start = idx_4 + 4
            else:
                nal_start = idx_3 + 3

            # Find next start code for NAL unit size
            next_idx_4 = data.find(start_code, nal_start)
            next_idx_3 = data.find(start_code_3, nal_start)

            if next_idx_4 == -1:
                next_pos = next_idx_3
            elif next_idx_3 == -1:
                next_pos = next_idx_4
            else:
                next_pos = min(next_idx_4, next_idx_3)

            if next_pos == -1:
                nal_data = data[nal_start:]
            else:
                nal_data = data[nal_start:next_pos]

            if len(nal_data) > 0:
                nal_type = NALAnalyzer._get_nal_type(nal_data[0], codec)
                nal_units.append(NALUnit(nal_data, nal_type, nal_start - 4))

            if next_pos == -1:
                break
            pos = next_pos

        return nal_units

    @staticmethod
    def _get_nal_type(first_byte: int, codec: str) -> int:
        """Extract NAL unit type from first byte."""
        if codec == "h264":
            return first_byte & 0x1F
        elif codec == "hevc" or codec == "vvc":
            return (first_byte >> 1) & 0x3F
        else:
            return first_byte

    @staticmethod
    def get_nal_type_name(nal_type: int, codec: str = "h264") -> str:
        """Get human-readable NAL type name."""
        if codec == "h264":
            return NALAnalyzer.H264_NAL_TYPES.get(nal_type, f"Unknown({nal_type})")
        elif codec == "hevc":
            return NALAnalyzer.HEVC_NAL_TYPES.get(nal_type, f"Unknown({nal_type})")
        else:
            return f"Type {nal_type}"


# Convenience exports
__all__ = [
    "NALAnalyzer",
    "NALUnit",
    "AVPacket",
    "AV_CODEC_ID_H264",
    "AV_CODEC_ID_HEVC",
    "AV_CODEC_ID_VVC",
    "AV_CODEC_ID_AV1",
    "_load_library",
]
