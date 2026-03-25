#!/bin/bash
# FFmpeg 硬件加速编译脚本 - 支持 QSV 和 NVDEC 解码
# 使用方法: 在 MSYS2 UCRT64 终端中运行此脚本

set -e

# 配置
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FFMPEG_REPO="${FFMPEG_REPO:-https://github.com/FFmpeg/FFmpeg.git}"
FFMPEG_BRANCH="${FFMPEG_BRANCH:-master}"
OUTPUT_DIR="${PROJECT_ROOT}/dist/ffmpeg-hwaccel"

# 编译器标志
export CC="gcc"
export CXX="g++"
export PKG_CONFIG="pkg-config"

# 静态链接标志
export CFLAGS="-static -static-libgcc -static-libstdc++ -O2 -pipe"
export CXXFLAGS="-static -static-libgcc -static-libstdc++ -O2 -pipe"
export LDFLAGS="-static -static-libgcc -static-libstdc++"
export PKG_CONFIG_PATH="/ucrt64/lib/pkgconfig"

# 硬件加速选项 (可通过环境变量覆盖)
ENABLE_QSV="${ENABLE_QSV:-auto}"       # auto/yes/no
ENABLE_NVDEC="${ENABLE_NVDEC:-auto}"   # auto/yes/no
ENABLE_NVENC="${ENABLE_NVENC:-auto}"   # auto/yes/no
ENABLE_D3D11VA="${ENABLE_D3D11VA:-yes}" # Windows D3D11 硬件加速
ENABLE_DXVA2="${ENABLE_DXVA2:-yes}"    # Windows DXVA2 硬件加速

echo "========================================"
echo "FFmpeg 硬件加速编译脚本"
echo "========================================"
echo "构建目录: ${BUILD_DIR}"
echo "输出目录: ${OUTPUT_DIR}"
echo ""
echo "硬件加速选项:"
echo "  QSV (Intel Quick Sync): ${ENABLE_QSV}"
echo "  NVDEC (NVIDIA 解码):    ${ENABLE_NVDEC}"
echo "  NVENC (NVIDIA 编码):    ${ENABLE_NVENC}"
echo "  D3D11VA:                ${ENABLE_D3D11VA}"
echo "  DXVA2:                  ${ENABLE_DXVA2}"
echo ""

# 检查是否在 MSYS2 UCRT64 环境
if [ -z "$MSYSTEM" ]; then
    echo "错误: 请在 MSYS2 UCRT64 终端中运行此脚本"
    exit 1
fi

if [ "$MSYSTEM" != "UCRT64" ]; then
    echo "警告: 当前环境是 $MSYSTEM，建议使用 UCRT64"
fi

# 构建配置参数
CONFIGURE_OPTS=""

# QSV 支持 (Intel Quick Sync Video)
# 注意: Windows 上 QSV 通常通过 Media SDK 或 oneVPL
# MSYS2 中可能没有预编译包，需要手动安装 Intel Media SDK
if [ "$ENABLE_QSV" = "yes" ]; then
    echo "检查 QSV 依赖..."
    if pkg-config --exists libmfx 2>/dev/null; then
        echo "  找到 libmfx"
        CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-libmfx"
    elif pkg-config --exists vpl 2>/dev/null; then
        echo "  找到 libvpl (oneVPL)"
        CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-libvpl"
    else
        echo "  警告: 未找到 libmfx 或 libvpl，QSV 将不可用"
        echo "  请安装 Intel Media SDK 或 oneVPL"
    fi
elif [ "$ENABLE_QSV" = "auto" ]; then
    # 自动检测
    if pkg-config --exists libmfx 2>/dev/null; then
        echo "检测到 libmfx，启用 QSV"
        CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-libmfx"
    elif pkg-config --exists vpl 2>/dev/null; then
        echo "检测到 libvpl，启用 QSV (oneVPL)"
        CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-libvpl"
    fi
fi

# NVDEC/NVENC 支持 (NVIDIA)
# NVDEC 在 FFmpeg 中默认自动检测，需要 ffnvcodec 头文件
# 在 Windows 上可以使用动态加载，不需要链接 nvcc 库
if [ "$ENABLE_NVDEC" = "no" ]; then
    CONFIGURE_OPTS="$CONFIGURE_OPTS --disable-nvdec"
fi

if [ "$ENABLE_NVENC" = "no" ]; then
    CONFIGURE_OPTS="$CONFIGURE_OPTS --disable-nvenc"
fi

# D3D11VA 和 DXVA2 (Windows 原生硬件加速)
# 这两个是 Windows 上最常用的硬件加速方式
if [ "$ENABLE_D3D11VA" = "yes" ]; then
    CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-d3d11va"
fi

if [ "$ENABLE_DXVA2" = "yes" ]; then
    CONFIGURE_OPTS="$CONFIGURE_OPTS --enable-dxva2"
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
echo "配置选项: ${CONFIGURE_OPTS}"
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
    --target-os=mingw64 \
    ${CONFIGURE_OPTS}

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

# 显示硬件加速支持情况
echo ""
echo "========================================"
echo "硬件加速支持情况"
echo "========================================"
echo "运行以下命令查看支持的硬件加速:"
echo "  ${OUTPUT_DIR}/bin/ffmpeg.exe -hwaccels"
echo ""
echo "运行以下命令查看支持的解码器:"
echo "  ${OUTPUT_DIR}/bin/ffmpeg.exe -decoders | grep -E '(cuvid|qsv|d3d11|dxva)'"
echo ""
echo "========================================"
echo "编译完成!"
echo "========================================"
echo "输出目录: ${OUTPUT_DIR}"
