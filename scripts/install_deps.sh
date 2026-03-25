#!/bin/bash
# 在 MSYS2 UCRT64 终端中运行此脚本安装编译依赖

echo "安装 FFmpeg 编译依赖..."

# 基础工具链
pacman -S --noconfirm --needed \
    mingw-w64-ucrt-x86_64-toolchain \
    mingw-w64-ucrt-x86_64-nasm \
    mingw-w64-ucrt-x86_64-yasm \
    mingw-w64-ucrt-x86_64-pkg-config \
    mingw-w64-ucrt-x86_64-SDL2 \
    git \
    make

echo ""
echo "========================================"
echo "可选依赖 - 硬件加速支持"
echo "========================================"
echo ""
echo "1. Intel QSV (Quick Sync Video) 支持:"
echo "   需要安装 Intel Media SDK 或 oneVPL"
echo "   下载地址: https://github.com/Intel-Media-SDK/MediaSDK"
echo "            https://github.com/oneapi-src/oneVPL"
echo ""
echo "2. NVIDIA NVDEC/NVENC 支持:"
echo "   需要安装 NVIDIA Video Codec SDK headers"
echo "   下载地址: https://github.com/FFmpeg/nv-codec-headers"
echo ""
echo "3. 常用编解码库 (可选):"
echo ""

read -r -p "是否安装可选编解码库? (y/N): " install_codecs
if [[ "$install_codecs" =~ ^[Yy]$ ]]; then
    pacman -S --noconfirm --needed \
        mingw-w64-ucrt-x86_64-libx264 \
        mingw-w64-ucrt-x86_64-libx265 \
        mingw-w64-ucrt-x86_64-fdk-aac \
        mingw-w64-ucrt-x86_64-lame \
        mingw-w64-ucrt-x86_64-opus \
        mingw-w64-ucrt-x86_64-libvorbis \
        mingw-w64-ucrt-x86_64-libvpx \
        mingw-w64-ucrt-x86_64-dav1d \
        mingw-w64-ucrt-x86_64-aom
fi

echo ""
echo "========================================"
echo "安装 NVIDIA nv-codec-headers (可选)"
echo "========================================"
echo ""
echo "NVIDIA 硬件加速需要 nv-codec-headers"
read -r -p "是否安装 nv-codec-headers? (y/N): " install_nv
if [[ "$install_nv" =~ ^[Yy]$ ]]; then
    BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
    NV_CODEC_DIR="${BUILD_DIR}/nv-codec-headers"

    echo "克隆 nv-codec-headers..."
    git clone https://github.com/FFmpeg/nv-codec-headers.git "${NV_CODEC_DIR}" 2>/dev/null || true
    cd "${NV_CODEC_DIR}" || exit 1
    git pull

    echo "安装 nv-codec-headers..."
    make install PREFIX=/ucrt64

    echo "nv-codec-headers 安装完成!"
fi

echo ""
echo "依赖安装完成!"
echo ""
echo "编译命令:"
echo "  ./build_static_ffmpeg.sh      # 基础编译"
echo "  ./build_ffmpeg_hwaccel.sh     # 硬件加速编译"
