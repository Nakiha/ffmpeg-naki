#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test demo for NakiNAL library.

Tests the NAL analysis library that statically links FFmpeg
and only exports naki_* symbols.
"""

import ctypes
import ctypes.util
import os
import sys
from pathlib import Path
from typing import List, Optional

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Paths
PROJECT_ROOT = Path(__file__).parent.resolve()
NAL_LIB_DIR = PROJECT_ROOT / "naki-nal-dist" / "bin"
FULL_BUILD_DIR = PROJECT_ROOT / "ffmpeg_full_build" / "bin"
TEST_VIDEO = PROJECT_ROOT / "resource" / "video" / "h264_9s_1920x1080.mp4"


# C structure definitions
class NalUnit(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
        ("type", ctypes.c_int),
        ("offset", ctypes.c_size_t),
        ("nuh_layer_id", ctypes.c_int),
        ("nuh_temporal_id", ctypes.c_int),
    ]


# Callback type
NalCallback = ctypes.CFUNCTYPE(None, ctypes.POINTER(NalUnit), ctypes.c_void_p)


class NakiNAL:
    """Python wrapper for NakiNAL library."""

    CODEC_H264 = 0
    CODEC_HEVC = 1
    CODEC_VVC = 2
    CODEC_AV1 = 3

    def __init__(self, lib_path: Optional[Path] = None):
        if lib_path is None:
            lib_path = NAL_LIB_DIR / "naki_nal.dll"

        if not lib_path.exists():
            raise FileNotFoundError(
                f"NakiNAL library not found: {lib_path}\n"
                "Please run: ./build_naki_nal.sh"
            )

        if sys.platform == "win32":
            os.add_dll_directory(str(lib_path.parent))

        self.lib = ctypes.CDLL(str(lib_path))
        self._setup_functions()
        self._nals = []  # Keep references to callback data

    def _setup_functions(self):
        # naki_nal_version
        self.lib.naki_nal_version.restype = ctypes.c_char_p
        self.lib.naki_nal_version.argtypes = []

        # naki_nal_version_number
        self.lib.naki_nal_version_number.restype = ctypes.c_uint32
        self.lib.naki_nal_version_number.argtypes = []

        # naki_nal_parser_create
        self.lib.naki_nal_parser_create.restype = ctypes.c_void_p
        self.lib.naki_nal_parser_create.argtypes = [ctypes.c_int]

        # naki_nal_parser_free
        self.lib.naki_nal_parser_free.restype = None
        self.lib.naki_nal_parser_free.argtypes = [ctypes.c_void_p]

        # naki_nal_parse
        self.lib.naki_nal_parse.restype = ctypes.c_int
        self.lib.naki_nal_parse.argtypes = [
            ctypes.c_void_p,  # parser
            ctypes.POINTER(ctypes.c_uint8),  # data
            ctypes.c_size_t,  # size
            NalCallback,  # callback
            ctypes.c_void_p,  # userdata
        ]

        # naki_nal_type_name
        self.lib.naki_nal_type_name.restype = ctypes.c_char_p
        self.lib.naki_nal_type_name.argtypes = [ctypes.c_int, ctypes.c_int]

        # naki_nal_find_units
        self.lib.naki_nal_find_units.restype = ctypes.c_int
        self.lib.naki_nal_find_units.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.c_int,
            ctypes.POINTER(ctypes.POINTER(NalUnit)),
            ctypes.POINTER(ctypes.c_size_t),
        ]

        # naki_nal_free_units
        self.lib.naki_nal_free_units.restype = None
        self.lib.nal_nal_free_units.argtypes = [ctypes.POINTER(NalUnit)]

    @property
    def version(self) -> str:
        return self.lib.naki_nal_version().decode()

    @property
    def version_number(self) -> tuple:
        v = self.lib.naki_nal_version_number()
        return (v >> 16, (v >> 8) & 0xFF, v & 0xFF)

    def get_nal_type_name(self, nal_type: int, codec: int) -> str:
        return self.lib.naki_nal_type_name(nal_type, codec).decode()

    def find_nal_units(self, data: bytes, codec: int) -> List[dict]:
        """
        Find NAL units in data.

        Returns a list of dicts with NAL info.
        """
        nals_ptr = ctypes.POINTER(NalUnit)()
        count = ctypes.c_size_t()

        result = self.lib.naki_nal_find_units(
            (ctypes.c_uint8 * len(data))(*data),
            len(data),
            codec,
            ctypes.byref(nals_ptr),
            ctypes.byref(count)
        )

        if result < 0:
            return []

        nals = []
        for i in range(count.value):
            nal = nals_ptr[i]
            nals.append({
                "type": nal.type,
                "size": nal.size,
                "offset": nal.offset,
                "layer_id": nal.nuh_layer_id,
                "temporal_id": nal.nuh_temporal_id,
            })

        # Free the array
        self.lib.naki_nal_free_units(nals_ptr)

        return nals


def test_naki_nal():
    """Test the NakiNAL library."""
    print("\n" + "=" * 60)
    print("Testing NakiNAL Library")
    print("=" * 60)

    if not NAL_LIB_DIR.exists():
        print(f"  Library not found: {NAL_LIB_DIR}")
        print("  Please run: ./build_naki_nal.sh")
        return False

    try:
        nal = NakiNAL()
        print(f"  Version: {nal.version}")
        print(f"  Version number: {'.'.join(map(str, nal.version_number))}")

        # Test with raw H.264 Annex B data (create test data)
        # SPS NAL: 00 00 00 01 67 ...
        # PPS NAL: 00 00 00 01 68 ...
        # IDR NAL: 00 00 00 01 65 ...
        test_data = bytes([
            0x00, 0x00, 0x00, 0x01, 0x67, 0x42, 0x00, 0x1e, 0x89, 0x8b, 0x60, 0x50,  # SPS
            0x00, 0x00, 0x00, 0x01, 0x68, 0xce, 0x3c, 0x80,  # PPS
            0x00, 0x00, 0x00, 0x01, 0x65, 0x88, 0x80, 0x10, 0x00, 0x00, 0x03, 0x00,  # IDR
        ])

        print("\n  Testing NAL parsing with synthetic data...")
        nals = nal.find_nal_units(test_data, NakiNAL.CODEC_H264)
        print(f"  Found {len(nals)} NAL units:")

        for i, n in enumerate(nals):
            type_name = nal.get_nal_type_name(n["type"], NakiNAL.CODEC_H264)
            print(f"    [{i}] Type {n['type']:2d} ({type_name:15s}): {n['size']:3d} bytes @ offset {n['offset']}")

        print("\n  NakiNAL library works!")
        return True

    except Exception as e:
        print(f"  Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dual_loading():
    """Test that NakiNAL and Full Build can coexist."""
    print("\n" + "=" * 60)
    print("Testing Dual Library Loading")
    print("=" * 60)

    results = {"full": False, "naki": False}

    # Load full build first
    if FULL_BUILD_DIR.exists():
        print("\n[1] Loading FFmpeg Full Build...")
        try:
            if sys.platform == "win32":
                os.add_dll_directory(str(FULL_BUILD_DIR))

            full_lib = ctypes.CDLL(str(FULL_BUILD_DIR / "avutil-60.dll"))
            full_lib.av_version_info.restype = ctypes.c_char_p
            print(f"  Full build: {full_lib.av_version_info().decode()}")
            results["full"] = True
        except Exception as e:
            print(f"  Failed: {e}")

    # Then load NakiNAL
    if NAL_LIB_DIR.exists():
        print("\n[2] Loading NakiNAL (alongside Full Build)...")
        try:
            if sys.platform == "win32":
                os.add_dll_directory(str(NAL_LIB_DIR))

            naki_lib = ctypes.CDLL(str(NAL_LIB_DIR / "naki_nal.dll"))
            naki_lib.naki_nal_version.restype = ctypes.c_char_p
            print(f"  NakiNAL: {naki_lib.naki_nal_version().decode()}")
            results["naki"] = True
        except Exception as e:
            print(f"  Failed: {e}")

    # Verify no symbol conflicts
    if results["full"] and results["naki"]:
        print("\n  SUCCESS: Both libraries loaded without conflicts!")
        print("  NakiNAL's FFmpeg symbols are hidden (statically linked)")

    return all(results.values())


def check_exported_symbols():
    """Check what symbols are exported by naki_nal.dll."""
    print("\n" + "=" * 60)
    print("Checking Exported Symbols")
    print("=" * 60)

    dll_path = NAL_LIB_DIR / "naki_nal.dll"
    if not dll_path.exists():
        print(f"  DLL not found: {dll_path}")
        return

    import subprocess

    print(f"\n  Checking {dll_path.name}...")

    # Get all exported symbols
    result = subprocess.run(
        ["objdump", "-p", str(dll_path)],
        capture_output=True,
        text=True
    )

    output = result.stdout

    # Look for naki_* symbols
    naki_symbols = [line for line in output.split('\n') if 'naki_' in line]
    print(f"\n  NakiNAL symbols ({len(naki_symbols)}):")
    for sym in naki_symbols[:15]:
        print(f"    {sym.strip()}")

    # Look for FFmpeg symbols (should be none)
    ffmpeg_symbols = [line for line in output.split('\n')
                      if any(x in line.lower() for x in ['avcodec', 'avutil', 'swresample', 'avformat'])]

    print(f"\n  FFmpeg symbols ({len(ffmpeg_symbols)}):")
    if ffmpeg_symbols:
        for sym in ffmpeg_symbols[:10]:
            print(f"    {sym.strip()}")
        print("  WARNING: FFmpeg symbols are exported!")
    else:
        print("    None - Good! FFmpeg symbols are hidden")


def main():
    print("=" * 60)
    print("NakiNAL Test Demo")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"NakiNAL lib:  {NAL_LIB_DIR}")
    print(f"Full build:   {FULL_BUILD_DIR}")

    naki_ok = test_naki_nal()
    dual_ok = test_dual_loading()

    if NAL_LIB_DIR.exists():
        check_exported_symbols()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  NakiNAL Test:       {'PASS' if naki_ok else 'FAIL / NOT BUILT'}")
    print(f"  Dual Loading Test:  {'PASS' if dual_ok else 'PARTIAL'}")


if __name__ == "__main__":
    main()
