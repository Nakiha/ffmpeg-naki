"""
NakiFFmpeg - NAL Analysis Library

A Python wrapper for NakiNAL, providing pure software NAL analysis
without conflicting with hardware-accelerated FFmpeg installations.
"""

from pathlib import Path
from typing import List, Optional
import ctypes
import os
import sys

# 类型定义
CODEC_H264 = 0
CODEC_HEVC = 1
CODEC_VVC = 2
CODEC_AV1 = 3

# 找到 DLL
def _find_dll() -> Path:
    """Find naki_nal.dll"""
    # 1. 包目录
    pkg_dir = Path(__file__).parent
    dll_path = pkg_dir / "naki_nal.dll"
    if dll_path.exists():
        return dll_path

    # 2. 构建目录
    root = pkg_dir.parent
    for pattern in ["build/cmake/bin/naki_nal.dll", "build/bin/naki_nal.dll"]:
        dll_path = root / pattern
        if dll_path.exists():
            return dll_path

    raise RuntimeError(
        "naki_nal.dll not found. Please build the library first:\n"
        "  pip install .\n"
        "  or: cmake -B build && cmake --build build"
    )


# 加载库
_lib: Optional[ctypes.CDLL] = None


def _get_lib() -> ctypes.CDLL:
    global _lib
    if _lib is None:
        dll_path = _find_dll()
        if sys.platform == "win32":
            os.add_dll_directory(str(dll_path.parent))
        _lib = ctypes.CDLL(str(dll_path))
        _setup_functions(_lib)
    return _lib


def _setup_functions(lib: ctypes.CDLL):
    """Setup function signatures"""
    lib.naki_nal_version.restype = ctypes.c_char_p
    lib.naki_nal_version.argtypes = []

    lib.naki_nal_version_number.restype = ctypes.c_uint32
    lib.naki_nal_version_number.argtypes = []

    lib.naki_nal_type_name.restype = ctypes.c_char_p
    lib.naki_nal_type_name.argtypes = [ctypes.c_int, ctypes.c_int]

    lib.naki_nal_parser_create.restype = ctypes.c_void_p
    lib.naki_nal_parser_create.argtypes = [ctypes.c_int]

    lib.naki_nal_parser_free.restype = None
    lib.naki_nal_parser_free.argtypes = [ctypes.c_void_p]


def version() -> str:
    """Get library version string"""
    return _get_lib().naki_nal_version().decode()


def version_number() -> tuple:
    """Get library version as (major, minor, patch)"""
    v = _get_lib().naki_nal_version_number()
    return (v >> 16, (v >> 8) & 0xFF, v & 0xFF)


def nal_type_name(nal_type: int, codec: int = CODEC_H264) -> str:
    """Get NAL unit type name"""
    return _get_lib().naki_nal_type_name(nal_type, codec).decode()


class NalUnit:
    """NAL unit information"""

    def __init__(self, type: int, size: int, offset: int,
                 layer_id: int = 0, temporal_id: int = 0):
        self.type = type
        self.size = size
        self.offset = offset
        self.layer_id = layer_id
        self.temporal_id = temporal_id

    def __repr__(self):
        return f"NalUnit(type={self.type}, size={self.size}, offset={self.offset})"


class NalParser:
    """NAL unit parser"""

    def __init__(self, codec: int = CODEC_H264):
        self._codec = codec
        self._parser = _get_lib().naki_nal_parser_create(codec)
        if not self._parser:
            raise RuntimeError("Failed to create NAL parser")

    def __del__(self):
        if hasattr(self, '_parser') and self._parser:
            _get_lib().naki_nal_parser_free(self._parser)

    def parse(self, data: bytes) -> List[NalUnit]:
        """Parse NAL units from data"""
        # 使用 Python 实现的简化解析
        return self._find_nal_units(data, self._codec)

    @staticmethod
    def _find_nal_units(data: bytes, codec: int) -> List[NalUnit]:
        """Find NAL units in Annex B format data"""
        nals = []
        start_code = b'\x00\x00\x00\x01'
        start_code_3 = b'\x00\x00\x01'

        pos = 0
        while pos < len(data):
            # Find start code
            idx_4 = data.find(start_code, pos)
            idx_3 = data.find(start_code_3, pos)

            if idx_4 == -1 and idx_3 == -1:
                break

            # Prefer 4-byte start code
            if idx_4 != -1 and (idx_3 == -1 or idx_4 <= idx_3):
                nal_start = idx_4 + 4
            else:
                nal_start = idx_3 + 3

            # Find next start code
            next_idx_4 = data.find(start_code, nal_start)
            next_idx_3 = data.find(start_code_3, nal_start)

            if next_idx_4 == -1:
                next_pos = next_idx_3
            elif next_idx_3 == -1:
                next_pos = next_idx_4
            else:
                next_pos = min(next_idx_4, next_idx_3)

            if next_pos == -1:
                nal_size = len(data) - nal_start
            else:
                nal_size = next_pos - nal_start

            if nal_size > 0:
                nal_type = NalParser._get_nal_type(data[nal_start], codec)
                nals.append(NalUnit(type=nal_type, size=nal_size, offset=nal_start))

            pos = nal_start + nal_size if next_pos == -1 else next_pos

        return nals

    @staticmethod
    def _get_nal_type(first_byte: int, codec: int) -> int:
        """Extract NAL type from first byte"""
        if codec == CODEC_H264:
            return first_byte & 0x1F
        elif codec in (CODEC_HEVC, CODEC_VVC):
            return (first_byte >> 1) & 0x3F
        return first_byte


__all__ = [
    "version", "version_number", "nal_type_name",
    "NalParser", "NalUnit",
    "CODEC_H264", "CODEC_HEVC", "CODEC_VVC", "CODEC_AV1",
]
