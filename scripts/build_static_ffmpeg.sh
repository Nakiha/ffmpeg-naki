#!/bin/bash
# FFmpeg 静态编译脚本 - 生成可分发的 Windows 二进制文件
# 使用方法: 在 MSYS2 UCRT64 终端中运行此脚本

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FFMPEG_REPO="${FFMPEG_REPO:-https://github.com/FFmpeg/FFmpeg.git}"
FFMPEG_BRANCH="${FFMPEG_BRANCH:-master}"
OUTPUT_DIR="${PROJECT_ROOT}/dist/ffmpeg-static"

# 编译器标志 - 关键是静态链接
export CC="gcc"
export CXX="g++"
export PKG_CONFIG="pkg-config"

# 静态链接标志 - 避免 MSYS2 DLL 依赖
export CFLAGS="-static -static-libgcc -static-libstdc++ -O2 -pipe"
export CXXFLAGS="-static -static-libgcc -static-libstdc++ -O2 -pipe"
export LDFLAGS="-static -static-libgcc -static-libstdc++"
export PKG_CONFIG_PATH="/ucrt64/lib/pkgconfig"

echo "========================================"
echo "FFmpeg 静态编译脚本"
echo "========================================"
echo "构建目录: ${BUILD_DIR}"
echo "输出目录: ${OUTPUT_DIR}"
echo ""

# 检查是否在 MSYS2 UCRT64 环境
if [ -z "$MSYSTEM" ]; then
    echo "错误: 请在 MSYS2 UCRT64 终端中运行此脚本"
    exit 1
fi

if [ "$MSYSTEM" != "UCRT64" ]; then
    echo "警告: 当前环境是 $MSYSTEM，建议使用 UCRT64"
fi

# 进入 FFmpeg 源码目录
if [ -d "ffmpeg" ]; then
    echo "进入 FFmpeg 源码目录..."
    cd ffmpeg
else
    echo "错误: ffmpeg 目录不存在，请先克隆源码"
    exit 1
fi

# 配置 FFmpeg
echo ""
echo "配置 FFmpeg..."
./configure \
    --prefix="${OUTPUT_DIR}" \
    --enable-gpl \
    --enable-version3 \
    --enable-static \
    --disable-shared \
    --disable-debug \
    --disable-doc \
    --disable-w32threads \
    --enable-pthreads \
    --pkg-config-flags="--static" \
    --extra-cflags="${CFLAGS}" \
    --extra-cxxflags="${CXXFLAGS}" \
    --extra-ldflags="${LDFLAGS}" \
    --extra-libs="-lws2_32 -lsecur32 -lbcrypt -lole32 -luser32 -lgdi32 -liphlpapi" \
    --arch=x86_64 \
    --target-os=mingw64

# 编译
echo ""
echo "编译 FFmpeg (使用 $(nproc) 个核心)..."
make -j$(nproc)

# 安装
echo ""
echo "安装到 ${OUTPUT_DIR}..."
make install

# Strip 二进制文件以减小体积
echo ""
echo "Strip 二进制文件..."
strip "${OUTPUT_DIR}/bin/ffmpeg.exe"
strip "${OUTPUT_DIR}/bin/ffprobe.exe"

# 检查依赖
echo ""
echo "========================================"
echo "检查 DLL 依赖..."
echo "========================================"
echo "ffmpeg.exe 依赖:"
objdump -p "${OUTPUT_DIR}/bin/ffmpeg.exe" | grep "DLL Name" | head -20

echo ""
echo "========================================"
echo "编译完成!"
echo "========================================"
echo "输出目录: ${OUTPUT_DIR}"
echo ""
echo "如果依赖中只包含 Windows 系统 DLL (如 KERNEL32.dll, msvcrt.dll 等)，"
echo "则表示编译成功，可以分发。"
