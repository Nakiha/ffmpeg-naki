#!/usr/bin/env python3
"""
FFmpeg NAKI Software-Only Build Script
=======================================

This script builds a software-only FFmpeg version with symbol prefix
to avoid DLL conflicts with other FFmpeg installations.

Features:
- Pure software decoding (no hardware acceleration)
- Symbol prefix "naki_" to avoid conflicts
- Python-friendly shared library output
- NAL analysis focus

Usage:
    python build_naki_soft.py [--clean] [--release]

Requirements:
    - MSYS2 UCRT64 environment
    - Or Visual Studio with CMake

Author: Nakiha
"""

import subprocess
import os
import sys
import shutil
import argparse
from pathlib import Path

# Configuration
BUILD_DIR = Path(__file__).parent.resolve()
FFMPEG_DIR = BUILD_DIR / "ffmpeg"
OUTPUT_DIR = BUILD_DIR / "ffmpeg-dist-naki"
SYMBOL_PREFIX = "naki_"

# MSYS2 paths (adjust if needed)
MSYS2_ROOT = Path("C:/msys64")
UCRT64_ROOT = MSYS2_ROOT / "ucrt64"


def run_cmd(cmd, cwd=None, env=None):
    """Run command and handle errors."""
    print(f"[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        shell=isinstance(cmd, str)
    )
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with code {result.returncode}")
    return result


def clean_build():
    """Clean build artifacts."""
    print("[*] Cleaning build artifacts...")

    dirs_to_clean = [OUTPUT_DIR]
    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
            print(f"  Removed {d}")

    # Clean FFmpeg build artifacts
    if FFMPEG_DIR.exists():
        clean_files = [
            "ffmpeg", "ffmpeg_g", "ffprobe", "ffprobe_g",
            "config.mak", "config.h", "version.h"
        ]
        for f in clean_files:
            fp = FFMPEG_DIR / f
            if fp.exists():
                if fp.is_dir():
                    shutil.rmtree(fp)
                else:
                    fp.unlink()

        # Clean library directories
        for lib_dir in FFMPEG_DIR.glob("lib*"):
            for ext in ["*.o", "*.a", "*.dll", "*.lib", "*.exp", "*.pdb"]:
                for f in lib_dir.glob(ext):
                    f.unlink()

        print("  Cleaned FFmpeg build artifacts")


def configure_msys_env():
    """Configure environment for MSYS2 UCRT64 build."""
    env = os.environ.copy()

    # Set up UCRT64 paths
    env["PATH"] = f"{UCRT64_ROOT / 'bin'};{env.get('PATH', '')}"
    env["CC"] = "gcc"
    env["CXX"] = "g++"
    env["PKG_CONFIG"] = "pkg-config"
    env["PKG_CONFIG_PATH"] = str(UCRT64_ROOT / "lib" / "pkgconfig")

    # Compiler flags for shared library with symbol prefix
    cflags = f"-O2 -pipe -DPREFIX={SYMBOL_PREFIX}"
    ldflags = "-shared"

    env["CFLAGS"] = cflags
    env["CXXFLAGS"] = cflags
    env["LDFLAGS"] = ldflags

    return env


def get_configure_args():
    """Get FFmpeg configure arguments for software-only NAL analysis build."""

    args = [
        f"--prefix={OUTPUT_DIR}",

        # License
        "--enable-gpl",
        "--enable-version3",

        # Build type - shared libraries for Python
        "--enable-shared",
        "--disable-static",

        # Disable unnecessary features
        "--disable-debug",
        "--disable-doc",
        "--disable-ffplay",
        "--disable-ffprobe",
        "--disable-network",

        # Threading
        "--disable-w32threads",
        "--enable-pthreads",

        # DISABLE ALL HARDWARE ACCELERATION
        "--disable-d3d11va",
        "--disable-dxva2",
        "--disable-nvdec",
        "--disable-nvenc",
        "--disable-cuda",
        "--disable-cuvid",
        "--disable-nvenc",
        "--disable-hwaccels",
        "--disable-libmfx",
        "--disable-libvpl",

        # Enable software decoders needed for NAL analysis
        "--enable-decoder=h264",
        "--enable-decoder=hevc",
        "--enable-decoder=vvc",
        "--enable-decoder=av1",
        "--enable-decoder=aac",
        "--enable-decoder=mp3",

        # Enable demuxers for container parsing
        "--enable-demuxer=h264",
        "--enable-demuxer=hevc",
        "--enable-demuxer=vvc",
        "--enable-demuxer=av1",
        "--enable-demuxer=mp4",
        "--enable-demuxer=matroska",
        "--enable-demuxer=flv",

        # Enable parsers for NAL analysis
        "--enable-parser=h264",
        "--enable-parser=hevc",
        "--enable-parser=vvc",
        "--enable-parser=av1",
        "--enable-parser=aac",

        # Enable bitstream filters for NAL manipulation
        "--enable-bsf=h264_metadata",
        "--enable-bsf=hevc_metadata",
        "--enable-bsf=vvc_metadata",
        "--enable-bsf=av1_metadata",
        "--enable-bsf=extract_extradata",
        "--enable-bsf=trace_headers",

        # Enable protocols for file I/O
        "--enable-protocol=file",

        # Symbol prefix for avoiding conflicts
        f"--prefix-symbols={SYMBOL_PREFIX}",

        # Architecture
        "--arch=x86_64",
        "--target-os=mingw64",

        # Additional flags
        "--pkg-config-flags=--static",
        f"--extra-cflags=-O2 -pipe -DPREFIX={SYMBOL_PREFIX}",
        "--extra-ldflags=-static-libgcc -static-libstdc++",
        "--extra-libs=-lws2_32 -lsecur32 -lbcrypt -lole32 -luser32 -lgdi32",
    ]

    return args


def build_with_msys2(clean=False):
    """Build using MSYS2 UCRT64 toolchain."""

    if clean:
        clean_build()

    print("\n" + "=" * 60)
    print("FFmpeg NAKI Software-Only Build")
    print("=" * 60)
    print(f"Build directory: {BUILD_DIR}")
    print(f"FFmpeg source:   {FFMPEG_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Symbol prefix:   {SYMBOL_PREFIX}")
    print("=" * 60 + "\n")

    if not FFMPEG_DIR.exists():
        print("[!] FFmpeg source not found. Please run: git submodule update --init")
        sys.exit(1)

    env = configure_msys_env()

    # Check MSYS2 environment
    if not UCRT64_ROOT.exists():
        print(f"[!] MSYS2 UCRT64 not found at {UCRT64_ROOT}")
        print("    Please install MSYS2 or use Visual Studio build")
        sys.exit(1)

    os.chdir(FFMPEG_DIR)

    # Configure
    print("[*] Configuring FFmpeg...")
    configure_args = get_configure_args()
    cmd = ["sh", "./configure"] + configure_args
    run_cmd(cmd, env=env)

    # Build
    print("\n[*] Building FFmpeg...")
    nproc = os.cpu_count() or 4
    run_cmd(["make", f"-j{nproc}"], env=env)

    # Install
    print("\n[*] Installing...")
    run_cmd(["make", "install"], env=env)

    # Rename output libraries with naki prefix
    print("\n[*] Renaming libraries with naki prefix...")
    rename_libraries()

    print("\n" + "=" * 60)
    print("Build completed successfully!")
    print("=" * 60)
    print(f"Output: {OUTPUT_DIR}")
    print(f"\nLibraries:")
    for lib in (OUTPUT_DIR / "bin").glob("*.dll"):
        print(f"  {lib.name}")
    print(f"\nTo use in Python:")
    print(f"  import ctypes")
    print(f"  lib = ctypes.CDLL(r'{OUTPUT_DIR / 'bin' / 'nakiavcodec.dll'}')")


def rename_libraries():
    """Rename output libraries with naki prefix."""
    bin_dir = OUTPUT_DIR / "bin"
    lib_dir = OUTPUT_DIR / "lib"

    renames = {
        "avcodec": "nakiavcodec",
        "avformat": "nakiavformat",
        "avutil": "nakiavutil",
        "swscale": "nakiswscale",
        "swresample": "nakiswresample",
        "postproc": "nakipostproc",
        "avfilter": "nakiavfilter",
        "avdevice": "nakiavdevice",
    }

    for old_name, new_name in renames.items():
        # Rename DLLs
        for ext in [".dll"]:
            old_path = bin_dir / f"{old_name}{ext}"
            new_path = bin_dir / f"{new_name}{ext}"
            if old_path.exists() and not new_path.exists():
                shutil.move(old_path, new_path)
                print(f"  {old_path.name} -> {new_path.name}")

        # Rename import libraries
        for ext in [".lib", ".dll.a"]:
            old_path = lib_dir / f"{old_name}{ext}"
            new_path = lib_dir / f"{new_name}{ext}"
            if old_path.exists() and not new_path.exists():
                shutil.move(old_path, new_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build FFmpeg NAKI software-only version"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--release",
        action="store_true",
        help="Build with release optimizations"
    )

    args = parser.parse_args()

    build_with_msys2(clean=args.clean)


if __name__ == "__main__":
    main()
