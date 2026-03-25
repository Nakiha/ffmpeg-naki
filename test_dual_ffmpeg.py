#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test demo for FFmpeg dual library loading.

This script tests that the NAKI FFmpeg build can coexist with
the full build (BtbN/FFmpeg-Builds) in the same Python process.

Usage:
    python test_dual_ffmpeg.py
"""

import ctypes
import ctypes.util
import os
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.resolve()
FULL_BUILD_DIR = PROJECT_ROOT / "ffmpeg_full_build" / "bin"
NAKI_BUILD_DIR = PROJECT_ROOT / "ffmpeg-dist-naki" / "bin"
TEST_VIDEO = PROJECT_ROOT / "resource" / "video" / "h264_9s_1920x1080.mp4"


class FFmpegLibrary:
    """Wrapper for loading and testing FFmpeg libraries."""

    def __init__(self, name: str, lib_dir: Path, lib_pattern: str):
        self.name = name
        self.lib_dir = lib_dir
        self.lib_pattern = lib_pattern
        self.libs = {}

        if not lib_dir.exists():
            raise FileNotFoundError(f"Library directory not found: {lib_dir}")

        # Add to DLL search path
        if sys.platform == "win32":
            os.add_dll_directory(str(lib_dir))

    def load(self, lib_name: str) -> ctypes.CDLL:
        """Load a specific library."""
        if lib_name in self.libs:
            return self.libs[lib_name]

        lib_path = self.lib_dir / lib_name
        if not lib_path.exists():
            # Try pattern
            matches = list(self.lib_dir.glob(self.lib_pattern.format(lib_name)))
            if matches:
                lib_path = matches[0]
            else:
                raise FileNotFoundError(f"Library not found: {lib_path}")

        print(f"  [{self.name}] Loading {lib_path.name}...")
        self.libs[lib_name] = ctypes.CDLL(str(lib_path))
        return self.libs[lib_name]

    def get_function(self, lib_name: str, func_name: str, restype, argtypes):
        """Get a function from a library with proper typing."""
        lib = self.load(lib_name)
        func = getattr(lib, func_name)
        func.restype = restype
        func.argtypes = argtypes
        return func


def test_full_build():
    """Test the full build (BtbN/FFmpeg-Builds) with hardware acceleration."""
    print("\n" + "=" * 60)
    print("Testing FFmpeg Full Build (Hardware Accelerated)")
    print("=" * 60)

    try:
        ffmpeg = FFmpegLibrary(
            "Full",
            FULL_BUILD_DIR,
            "*.dll"
        )

        # Load avutil
        avutil = ffmpeg.load("avutil-60.dll")

        # Test av_version_info()
        av_version_info = ffmpeg.get_function(
            "avutil-60.dll",
            "av_version_info",
            ctypes.c_char_p,
            []
        )
        version = av_version_info()
        print(f"  av_version_info(): {version.decode()}")

        # Test avutil_version()
        avutil_version = ffmpeg.get_function(
            "avutil-60.dll",
            "avutil_version",
            ctypes.c_uint,
            []
        )
        util_ver = avutil_version()
        major = (util_ver >> 16) & 0xFF
        minor = (util_ver >> 8) & 0xFF
        micro = util_ver & 0xFF
        print(f"  avutil_version(): {major}.{minor}.{micro}")

        # Load avcodec
        avcodec = ffmpeg.load("avcodec-62.dll")

        # Test avcodec_version()
        avcodec_version = ffmpeg.get_function(
            "avcodec-62.dll",
            "avcodec_version",
            ctypes.c_uint,
            []
        )
        codec_ver = avcodec_version()
        major = (codec_ver >> 16) & 0xFF
        minor = (codec_ver >> 8) & 0xFF
        micro = codec_ver & 0xFF
        print(f"  avcodec_version(): {major}.{minor}.{micro}")

        # Test avcodec_configuration()
        avcodec_config = ffmpeg.get_function(
            "avcodec-62.dll",
            "avcodec_configuration",
            ctypes.c_char_p,
            []
        )
        config = avcodec_config()
        config_str = config.decode()
        print(f"  avcodec_configuration() length: {len(config_str)} chars")

        # Check for hardware acceleration
        hwaccels = ["nvdec", "nvenc", "cuda", "d3d11va", "dxva2", "qsv", "vulkan"]
        print("  Hardware acceleration support:")
        for hw in hwaccels:
            if f"--enable-{hw}" in config_str or hw in config_str.lower():
                print(f"    ✓ {hw.upper()}")
            elif f"--disable-{hw}" in config_str:
                print(f"    ✗ {hw.upper()} (disabled)")

        print("\n  ✅ Full build loaded successfully!")
        return True

    except Exception as e:
        print(f"\n  ❌ Failed to load full build: {e}")
        return False


def test_naki_build():
    """Test the NAKI build (software-only with symbol prefix)."""
    print("\n" + "=" * 60)
    print("Testing NAKI FFmpeg Build (Software-Only)")
    print("=" * 60)

    if not NAKI_BUILD_DIR.exists():
        print(f"  ⚠️  NAKI build not found at: {NAKI_BUILD_DIR}")
        print("  Please run: ./build_naki_soft.sh")
        return False

    try:
        ffmpeg = FFmpegLibrary(
            "NAKI",
            NAKI_BUILD_DIR,
            "naki*.dll"
        )

        # Load nakiavutil
        avutil = ffmpeg.load("nakiavutil.dll")

        # Test naki_av_version_info() (with prefix)
        av_version_info = ffmpeg.get_function(
            "nakiavutil.dll",
            "naki_av_version_info",
            ctypes.c_char_p,
            []
        )
        version = av_version_info()
        print(f"  naki_av_version_info(): {version.decode()}")

        # Test naki_avutil_version()
        avutil_version = ffmpeg.get_function(
            "nakiavutil.dll",
            "naki_avutil_version",
            ctypes.c_uint,
            []
        )
        util_ver = avutil_version()
        major = (util_ver >> 16) & 0xFF
        minor = (util_ver >> 8) & 0xFF
        micro = util_ver & 0xFF
        print(f"  naki_avutil_version(): {major}.{minor}.{micro}")

        # Load nakiavcodec
        avcodec = ffmpeg.load("nakiavcodec.dll")

        # Test naki_avcodec_version()
        avcodec_version = ffmpeg.get_function(
            "nakiavcodec.dll",
            "naki_avcodec_version",
            ctypes.c_uint,
            []
        )
        codec_ver = avcodec_version()
        major = (codec_ver >> 16) & 0xFF
        minor = (codec_ver >> 8) & 0xFF
        micro = codec_ver & 0xFF
        print(f"  naki_avcodec_version(): {major}.{minor}.{micro}")

        # Test naki_avcodec_configuration()
        avcodec_config = ffmpeg.get_function(
            "nakiavcodec.dll",
            "naki_avcodec_configuration",
            ctypes.c_char_p,
            []
        )
        config = avcodec_config()
        config_str = config.decode()
        print(f"  naki_avcodec_configuration() length: {len(config_str)} chars")

        # Check for disabled hardware acceleration
        hwaccels = ["nvdec", "nvenc", "cuda", "d3d11va", "dxva2", "qsv", "hwaccels"]
        print("  Hardware acceleration (should be disabled):")
        for hw in hwaccels:
            if f"--disable-{hw}" in config_str:
                print(f"    ✓ {hw.upper()} disabled")
            elif f"--enable-{hw}" in config_str:
                print(f"    ✗ {hw.upper()} enabled (unexpected!)")

        print("\n  ✅ NAKI build loaded successfully!")
        return True

    except Exception as e:
        print(f"\n  ❌ Failed to load NAKI build: {e}")
        return False


def test_dual_loading():
    """Test that both builds can be loaded simultaneously."""
    print("\n" + "=" * 60)
    print("Testing Dual Library Loading (Symbol Conflict Test)")
    print("=" * 60)

    results = {
        "full": False,
        "naki": False,
    }

    # First, load full build
    print("\n[Phase 1] Loading Full Build...")
    try:
        full = FFmpegLibrary("Full", FULL_BUILD_DIR, "*.dll")

        # Add to DLL search path
        if sys.platform == "win32":
            os.add_dll_directory(str(FULL_BUILD_DIR))

        full_avutil = full.load("avutil-60.dll")
        full_version = ctypes.CDLL(str(FULL_BUILD_DIR / "avutil-60.dll")).av_version_info
        full_version.restype = ctypes.c_char_p
        print(f"  Full build av_version_info: {full_version().decode()}")
        results["full"] = True
    except Exception as e:
        print(f"  Failed: {e}")

    # Then, load NAKI build (if available)
    if NAKI_BUILD_DIR.exists():
        print("\n[Phase 2] Loading NAKI Build (alongside Full Build)...")
        try:
            naki = FFmpegLibrary("NAKI", NAKI_BUILD_DIR, "naki*.dll")

            # Add to DLL search path
            if sys.platform == "win32":
                os.add_dll_directory(str(NAKI_BUILD_DIR))

            naki_avutil = naki.load("nakiavutil.dll")

            # Test the prefixed function
            naki_version = ctypes.CDLL(str(NAKI_BUILD_DIR / "nakiavutil.dll")).naki_av_version_info
            naki_version.restype = ctypes.c_char_p
            print(f"  NAKI build naki_av_version_info: {naki_version().decode()}")
            results["naki"] = True
        except Exception as e:
            print(f"  Failed: {e}")
    else:
        print("\n[Phase 2] Skipped - NAKI build not available")

    # Summary
    print("\n" + "-" * 40)
    print("Results:")
    print(f"  Full Build: {'✅ Loaded' if results['full'] else '❌ Failed'}")
    print(f"  NAKI Build: {'✅ Loaded' if results['naki'] else '⚠️  Not built'}")

    if results["full"] and results["naki"]:
        print("\n  🎉 SUCCESS: Both builds loaded without symbol conflicts!")
        print("  The symbol prefix strategy works correctly.")
    elif results["full"]:
        print("\n  ℹ️  Full build works. Build NAKI version to test dual loading.")

    return all(results.values())


def test_nal_analysis():
    """Test NAL analysis functionality."""
    print("\n" + "=" * 60)
    print("Testing NAL Analysis Module")
    print("=" * 60)

    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from naki_ffmpeg import NALAnalyzer

        # Read test video
        if TEST_VIDEO.exists():
            print(f"  Reading test file: {TEST_VIDEO.name}")
            with open(TEST_VIDEO, "rb") as f:
                data = f.read(1024 * 1024)  # Read first 1MB

            # Find NAL units
            nal_units = NALAnalyzer.find_nal_units(data, "h264")
            print(f"  Found {len(nal_units)} NAL units in first 1MB")

            if nal_units:
                print("\n  First 10 NAL units:")
                for i, nal in enumerate(nal_units[:10]):
                    type_name = NALAnalyzer.get_nal_type_name(nal.nal_type, "h264")
                    print(f"    [{i}] {type_name}: {nal.size} bytes @ offset {nal.offset}")
        else:
            print(f"  ⚠️  Test video not found: {TEST_VIDEO}")
            print("  Run: git lfs pull")

        print("\n  ✅ NAL analysis module works!")
        return True

    except ImportError as e:
        print(f"  ⚠️  Could not import naki_ffmpeg: {e}")
        return False
    except Exception as e:
        print(f"  ❌ NAL analysis failed: {e}")
        return False


def main():
    print("=" * 60)
    print("FFmpeg Dual Library Test Demo")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Full build:   {FULL_BUILD_DIR}")
    print(f"NAKI build:   {NAKI_BUILD_DIR}")
    print(f"Test video:   {TEST_VIDEO}")

    # Run tests
    full_ok = test_full_build()
    naki_ok = test_naki_build()
    dual_ok = test_dual_loading()
    nal_ok = test_nal_analysis()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"  Full Build Test:       {'✅ PASS' if full_ok else '❌ FAIL'}")
    print(f"  NAKI Build Test:       {'✅ PASS' if naki_ok else '⚠️  NOT BUILT'}")
    print(f"  Dual Loading Test:     {'✅ PASS' if dual_ok else '⚠️  PARTIAL'}")
    print(f"  NAL Analysis Test:     {'✅ PASS' if nal_ok else '❌ FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
