#!/bin/bash
# ============================================================================
# Build FFmpeg Static Libraries
# ============================================================================
#
# 编译 FFmpeg 静态库供 NakiNAL 链接
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FFMPEG_DIR="${PROJECT_ROOT}/ffmpeg"
OUTPUT_DIR="${PROJECT_ROOT}/build/ffmpeg-static"

# 编译器标志
export CC="gcc"
export CXX="g++"
export PKG_CONFIG="pkg-config"
export CFLAGS="-O2 -pipe"
export CXXFLAGS="-O2 -pipe"
export LDFLAGS="-static-libgcc -static-libstdc++"
export PKG_CONFIG_PATH="/ucrt64/lib/pkgconfig"

echo "========================================"
echo "FFmpeg Static Build"
echo "========================================"
echo "源码:   ${FFMPEG_DIR}"
echo "输出:   ${OUTPUT_DIR}"
echo ""

# 检查 MSYS2
if [ -z "$MSYSTEM" ]; then
    echo "错误: 请在 MSYS2 UCRT64 终端中运行"
    exit 1
fi

if [ "$MSYSTEM" != "UCRT64" ]; then
    echo "警告: 当前环境是 $MSYSTEM，建议使用 UCRT64"
fi

# 检查源码
if [ ! -d "${FFMPEG_DIR}" ]; then
    echo "错误: FFmpeg 源码不存在"
    echo "运行: git submodule update --init"
    exit 1
fi

# 已存在则跳过
if [ -f "${OUTPUT_DIR}/lib/libavcodec.a" ]; then
    echo "FFmpeg 静态库已存在，跳过编译"
    echo "如需重新编译，删除: ${OUTPUT_DIR}"
    exit 0
fi

cd "${FFMPEG_DIR}"

echo "配置 FFmpeg..."
./configure \
    --prefix="${OUTPUT_DIR}" \
    --enable-gpl \
    --enable-version3 \
    --enable-static \
    --disable-shared \
    --disable-debug \
    --disable-doc \
    --disable-ffplay \
    --disable-ffprobe \
    --disable-ffmpeg \
    --disable-w32threads \
    --enable-pthreads \
    --disable-d3d11va \
    --disable-dxva2 \
    --disable-vaapi \
    --disable-vdpau \
    --disable-cuda \
    --disable-cuda-llvm \
    --disable-cuvid \
    --disable-nvdec \
    --disable-nvenc \
    --disable-hwaccels \
    --disable-encoders \
    --disable-muxers \
    --disable-filters \
    --disable-devices \
    --disable-network \
    --arch=x86_64 \
    --target-os=mingw64 \
    --pkg-config-flags="--static" \
    --extra-cflags="${CFLAGS}" \
    --extra-cxxflags="${CXXFLAGS}" \
    --extra-ldflags="${LDFLAGS}" \
    --extra-libs="-lws2_32 -lsecur32 -lbcrypt -lole32 -luser32 -lgdi32 -liphlpapi"

echo ""
echo "编译 (使用 $(nproc) 核心)..."
make -j$(nproc)

echo ""
echo "安装..."
make install

echo ""
echo "========================================"
echo "完成!"
echo "========================================"
ls -la "${OUTPUT_DIR}/lib/"*.a | head -5
