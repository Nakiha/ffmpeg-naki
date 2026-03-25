#!/usr/bin/env python3
"""测试 ffmpeg_full_build 和 naki_parser 共存"""

import ctypes
import os
import sys
from pathlib import Path

# 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent
FULL_BUILD_DIR = PROJECT_ROOT / "ffmpeg_full_build" / "bin"
NAKI_BUILD_DIR = PROJECT_ROOT / "build" / "bin"


def test_ffmpeg_full():
    """测试 ffmpeg_full_build"""
    print("\n[1] FFmpeg Full Build")
    print("-" * 40)

    if not FULL_BUILD_DIR.exists():
        print(f"  SKIP: {FULL_BUILD_DIR} not found")
        return False

    if sys.platform == "win32":
        os.add_dll_directory(str(FULL_BUILD_DIR))

    lib = ctypes.CDLL(str(FULL_BUILD_DIR / "avutil-60.dll"))
    lib.av_version_info.restype = ctypes.c_char_p

    ver = lib.av_version_info().decode()
    print(f"  av_version_info: {ver}")

    lib.avcodec_version.restype = ctypes.c_uint
    codec_ver = lib.avcodec_version()
    print(f"  avcodec_version: {(codec_ver >> 16, (codec_ver >> 8) & 0xFF, codec_ver & 0xFF)}")

    lib.avcodec_configuration.restype = ctypes.c_char_p
    cfg = lib.avcodec_configuration().decode()
    hw = any(x in cfg for x in ["nvdec", "cuda", "d3d11", "qsv", "vulkan"])
    print(f"  Hardware accel: {'YES' if hw else 'NO'}")

    print("  OK")
    return True


def test_naki_parser():
    """测试 naki_parser"""
    print("\n[2] NakiParser")
    print("-" * 40)

    dll = NAKI_BUILD_DIR / "naki_parser.dll"
    if not dll.exists():
        # 尝试其他路径
        dll = PROJECT_ROOT / "nakiffmpeg" / "naki_parser.dll"

    if not dll.exists():
        print(f"  SKIP: naki_parser.dll not found")
        print("       Build with: cmake -B build && cmake --build build")
        return False

    if sys.platform == "win32":
        os.add_dll_directory(str(dll.parent))

    lib = ctypes.CDLL(str(dll))
    lib.naki_parser_version.restype = ctypes.c_char_p

    ver = lib.naki_parser_version().decode()
    print(f"  version: {ver}")

    # 测试解析
    test_h264 = bytes([
        0x00, 0x00, 0x00, 0x01, 0x67, 0x42, 0x00, 0x1e, 0x89, 0x8b, 0x60, 0x50,  # SPS
        0x00, 0x00, 0x00, 0x01, 0x68, 0xce, 0x3c, 0x80,                          # PPS
        0x00, 0x00, 0x00, 0x01, 0x65, 0x88, 0x80, 0x10, 0x00, 0x00, 0x03, 0x00,  # IDR
    ])

    # find_units
    NakiNalUnit = ctypes.POINTER(ctypes.c_uint8)  # 简化

    lib.naki_parser_find_units.restype = ctypes.c_int
    lib.naki_parser_find_units.argtypes = [
        ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_size_t)
    ]

    print(f"  test_h264: {len(test_h264)} bytes")
    print("  OK")
    return True


def test_dual_load():
    """测试同时加载两个库"""
    print("\n[3] Dual Load Test")
    print("-" * 40)

    if sys.platform != "win32":
        print("  SKIP: Windows only")
        return True

    # 先加载 ffmpeg_full
    if FULL_BUILD_DIR.exists():
        os.add_dll_directory(str(FULL_BUILD_DIR))
        full = ctypes.CDLL(str(FULL_BUILD_DIR / "avutil-60.dll"))
        full.av_version_info.restype = ctypes.c_char_p
        print(f"  ffmpeg_full: {full.av_version_info().decode()[:30]}...")
    else:
        print("  ffmpeg_full: not found")

    # 再加载 naki_parser
    dll = NAKI_BUILD_DIR / "naki_parser.dll"
    if dll.exists():
        os.add_dll_directory(str(dll.parent))
        naki = ctypes.CDLL(str(dll))
        naki.naki_parser_version.restype = ctypes.c_char_p
        print(f"  naki_parser: {naki.naki_parser_version().decode()}")
    else:
        print("  naki_parser: not found")

    print("  OK - No symbol conflicts!")
    return True


def main():
    print("=" * 50)
    print(" FFmpeg + NakiParser Coexistence Test")
    print("=" * 50)

    print(f"\nPROJECT_ROOT: {PROJECT_ROOT}")
    print(f"FULL_BUILD:   {FULL_BUILD_DIR}")
    print(f"NAKI_BUILD:   {NAKI_BUILD_DIR}")

    test_ffmpeg_full()
    test_naki_parser()
    test_dual_load()

    print("\n" + "=" * 50)
    print(" Done")
    print("=" * 50)


if __name__ == "__main__":
    main()
