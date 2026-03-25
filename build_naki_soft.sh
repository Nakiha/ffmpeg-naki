#!/bin/bash
# ============================================================================
# FFmpeg NAKI Software-Only Build Script
# ============================================================================
#
# 纯软件解码版本，用于NAL分析，避免与硬件加速版本的DLL符号冲突
#
# 特点:
# - 禁用所有硬件加速 (D3D11VA, DXVA2, NVDEC, NVENC, QSV, CUDA)
# - 使用 naki_ 符号前缀避免DLL冲突
# - 输出共享库供Python调用
# - 专注于NAL分析和码流解析
#
# 使用方法:
#   在 MSYS2 UCRT64 终端中运行:
#   ./build_naki_soft.sh [--clean]
#
# ============================================================================

set -e

# 配置
BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
FFMPEG_DIR="${BUILD_DIR}/ffmpeg"
OUTPUT_DIR="${BUILD_DIR}/ffmpeg-dist-naki"
SYMBOL_PREFIX="naki_"

# 硬件加速选项 - 全部禁用
ENABLE_QSV="no"
ENABLE_NVDEC="no"
ENABLE_NVENC="no"
ENABLE_D3D11VA="no"
ENABLE_DXVA2="no"
ENABLE_CUDA="no"

# 编译器标志
export CC="gcc"
export CXX="g++"
export PKG_CONFIG="pkg-config"
export CFLAGS="-O2 -pipe -DPREFIX=${SYMBOL_PREFIX}"
export CXXFLAGS="-O2 -pipe -DPREFIX=${SYMBOL_PREFIX}"
export LDFLAGS="-static-libgcc -static-libstdc++"
export PKG_CONFIG_PATH="/ucrt64/lib/pkgconfig"

# 解析参数
CLEAN_BUILD=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "========================================"
echo "FFmpeg NAKI Software-Only Build"
echo "========================================"
echo "构建目录:   ${BUILD_DIR}"
echo "源码目录:   ${FFMPEG_DIR}"
echo "输出目录:   ${OUTPUT_DIR}"
echo "符号前缀:   ${SYMBOL_PREFIX}"
echo ""
echo "硬件加速:   全部禁用 (纯软件解码)"
echo "  D3D11VA:  ${ENABLE_D3D11VA}"
echo "  DXVA2:    ${ENABLE_DXVA2}"
echo "  NVDEC:    ${ENABLE_NVDEC}"
echo "  NVENC:    ${ENABLE_NVENC}"
echo "  QSV:      ${ENABLE_QSV}"
echo "  CUDA:     ${ENABLE_CUDA}"
echo ""

# 检查是否在 MSYS2 UCRT64 环境
if [ -z "$MSYSTEM" ]; then
    echo "错误: 请在 MSYS2 UCRT64 终端中运行此脚本"
    exit 1
fi

if [ "$MSYSTEM" != "UCRT64" ]; then
    echo "警告: 当前环境是 $MSYSTEM，建议使用 UCRT64"
fi

# 清理
if [ "$CLEAN_BUILD" = true ]; then
    echo "清理构建目录..."
    rm -rf "${OUTPUT_DIR}"
    if [ -d "${FFMPEG_DIR}" ]; then
        cd "${FFMPEG_DIR}"
        make clean 2>/dev/null || true
        rm -f config.mak config.h version.h
        rm -f ffmpeg ffmpeg_g ffprobe ffprobe_g
        for dir in libav*; do
            rm -f "$dir"/*.o "$dir"/*.a 2>/dev/null || true
        done
        cd "${BUILD_DIR}"
    fi
fi

# 检查 FFmpeg 源码
if [ ! -d "${FFMPEG_DIR}" ]; then
    echo "错误: FFmpeg 源码不存在"
    echo "请运行: git submodule update --init"
    exit 1
fi

cd "${FFMPEG_DIR}"

# 配置 FFmpeg
echo ""
echo "配置 FFmpeg..."

./configure \
    --prefix="${OUTPUT_DIR}" \
    \
    `# License` \
    --enable-gpl \
    --enable-version3 \
    \
    `# Build type - shared libraries` \
    --enable-shared \
    --disable-static \
    \
    `# Disable unnecessary features` \
    --disable-debug \
    --disable-doc \
    --disable-ffplay \
    --disable-ffprobe \
    \
    `# Threading` \
    --disable-w32threads \
    --enable-pthreads \
    \
    `# DISABLE ALL HARDWARE ACCELERATION` \
    --disable-d3d11va \
    --disable-dxva2 \
    --disable-nvdec \
    --disable-nvenc \
    --disable-cuda \
    --disable-cuvid \
    --disable-hwaccels \
    --disable-libmfx \
    --disable-libvpl \
    \
    `# Enable software decoders for NAL analysis` \
    --enable-decoder=h264 \
    --enable-decoder=hevc \
    --enable-decoder=vvc \
    --enable-decoder=av1 \
    --enable-decoder=aac,mp3 \
    \
    `# Enable demuxers` \
    --enable-demuxer=h264,hevc,vvc,av1 \
    --enable-demuxer=mp4,matroska,flv \
    \
    `# Enable parsers` \
    --enable-parser=h264,hevc,vvc,av1,aac \
    \
    `# Enable bitstream filters for NAL manipulation` \
    --enable-bsf=h264_metadata \
    --enable-bsf=hevc_metadata \
    --enable-bsf=vvc_metadata \
    --enable-bsf=av1_metadata \
    --enable-bsf=extract_extradata \
    --enable-bsf=trace_headers \
    \
    `# Enable protocols` \
    --enable-protocol=file \
    \
    `# Symbol prefix for avoiding conflicts` \
    --prefix-symbols="${SYMBOL_PREFIX}" \
    \
    `# Architecture` \
    --arch=x86_64 \
    --target-os=mingw64 \
    \
    `# Additional flags` \
    --pkg-config-flags="--static" \
    --extra-cflags="${CFLAGS}" \
    --extra-ldflags="${LDFLAGS}" \
    --extra-libs="-lws2_32 -lsecur32 -lbcrypt -lole32 -luser32 -lgdi32"

# 编译
echo ""
echo "编译 FFmpeg (使用 $(nproc) 个核心)..."
make -j$(nproc)

# 安装
echo ""
echo "安装到 ${OUTPUT_DIR}..."
make install

# 重命名库文件
echo ""
echo "重命名库文件..."
rename_library() {
    local old_name=$1
    local new_name=$2

    # 重命名 DLL
    if [ -f "${OUTPUT_DIR}/bin/${old_name}.dll" ]; then
        mv "${OUTPUT_DIR}/bin/${old_name}.dll" "${OUTPUT_DIR}/bin/${new_name}.dll"
        echo "  ${old_name}.dll -> ${new_name}.dll"
    fi

    # 重命名导入库
    if [ -f "${OUTPUT_DIR}/lib/${old_name}.dll.a" ]; then
        mv "${OUTPUT_DIR}/lib/${old_name}.dll.a" "${OUTPUT_DIR}/lib/${new_name}.dll.a"
    fi
}

rename_library "avcodec" "nakiavcodec"
rename_library "avformat" "nakiavformat"
rename_library "avutil" "nakiavutil"
rename_library "swscale" "nakiswscale"
rename_library "swresample" "nakiswresample"
rename_library "postproc" "nakipostproc"
rename_library "avfilter" "nakiavfilter"
rename_library "avdevice" "nakiavdevice"

# 检查输出
echo ""
echo "========================================"
echo "编译完成!"
echo "========================================"
echo "输出目录: ${OUTPUT_DIR}"
echo ""
echo "生成的 DLL:"
ls -la "${OUTPUT_DIR}/bin/"*.dll 2>/dev/null || echo "  (无 DLL 文件)"
echo ""
echo "Python 调用示例:"
echo "  import ctypes"
echo "  lib = ctypes.CDLL(r'${OUTPUT_DIR}/bin/nakiavcodec.dll')"
echo ""
echo "符号冲突避免:"
echo "  所有导出符号已添加 '${SYMBOL_PREFIX}' 前缀"
echo "  例如: avcodec_send_packet -> ${SYMBOL_PREFIX}avcodec_send_packet"
