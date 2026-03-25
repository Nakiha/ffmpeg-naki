#!/bin/bash
# ============================================================================
# NakiNAL Build Script
# ============================================================================
#
# 编译纯软件NAL分析库：
# 1. 静态编译FFmpeg（禁用硬件加速）
# 2. 编译NAL库，静态链接FFmpeg
# 3. 只导出naki_*符号，不导出FFmpeg符号
#
# 使用方法:
#   在 MSYS2 UCRT64 终端中运行:
#   cd scripts && ./build_naki_nal.sh [--clean]
#
# ============================================================================

set -e

# 配置 - 项目根目录是scripts的父目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FFMPEG_DIR="${PROJECT_ROOT}/ffmpeg"
SRC_DIR="${PROJECT_ROOT}/src"
OUTPUT_DIR="${PROJECT_ROOT}/dist/naki-nal"
FFMPEG_STATIC_DIR="${PROJECT_ROOT}/build/ffmpeg-static"

# 编译器标志
export CC="gcc"
export CXX="g++"
export PKG_CONFIG="pkg-config"
export CFLAGS="-O2 -pipe"
export CXXFLAGS="-O2 -pipe"
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
echo "NakiNAL Build Script"
echo "========================================"
echo "项目根目录:   ${PROJECT_ROOT}"
echo "FFmpeg源码:   ${FFMPEG_DIR}"
echo "源码目录:     ${SRC_DIR}"
echo "FFmpeg静态:   ${FFMPEG_STATIC_DIR}"
echo "输出目录:     ${OUTPUT_DIR}"
echo ""
echo "特点: 静态链接FFmpeg，只导出naki_*符号"
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
    rm -rf "${FFMPEG_STATIC_DIR}"
    rm -rf "${PROJECT_ROOT}/build"
    if [ -d "${FFMPEG_DIR}" ]; then
        cd "${FFMPEG_DIR}"
        make clean 2>/dev/null || true
        rm -f config.mak config.h version.h ffbuild/config.mak
    fi
fi

# 检查 FFmpeg 源码
if [ ! -d "${FFMPEG_DIR}" ]; then
    echo "错误: FFmpeg 源码不存在"
    echo "请运行: git submodule update --init"
    exit 1
fi

# 检查源码
if [ ! -f "${SRC_DIR}/naki_nal.c" ]; then
    echo "错误: 源码不存在 ${SRC_DIR}/naki_nal.c"
    exit 1
fi

# ========================================
# 阶段1: 编译静态FFmpeg
# ========================================
echo ""
echo "========================================"
echo "[1/2] 编译静态FFmpeg库..."
echo "========================================"

if [ ! -f "${FFMPEG_STATIC_DIR}/lib/libavcodec.a" ]; then
    cd "${FFMPEG_DIR}"

    echo "配置 FFmpeg (静态库, 无硬件加速)..."
    ./configure \
        --prefix="${FFMPEG_STATIC_DIR}" \
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

    echo "编译 FFmpeg (使用 $(nproc) 个核心)..."
    make -j$(nproc)

    echo "安装 FFmpeg 静态库..."
    make install
else
    echo "FFmpeg静态库已存在，跳过编译"
fi

# ========================================
# 阶段2: 编译NAL库
# ========================================
echo ""
echo "========================================"
echo "[2/2] 编译NakiNAL库..."
echo "========================================"

mkdir -p "${OUTPUT_DIR}/bin"
mkdir -p "${OUTPUT_DIR}/lib"
mkdir -p "${OUTPUT_DIR}/include"

# 编译NAL库的目标文件
echo "编译 naki_nal.c..."

gcc -c "${SRC_DIR}/naki_nal.c" -o "${PROJECT_ROOT}/build/naki_nal.o" \
    ${CFLAGS} \
    -I"${FFMPEG_STATIC_DIR}/include" \
    -DNAKI_NAL_BUILD

# 创建DEF文件（只导出naki_*符号）
echo "创建导出符号文件..."
mkdir -p "${PROJECT_ROOT}/build"
cat > "${PROJECT_ROOT}/build/naki_nal.def" << 'EOF'
LIBRARY naki_nal
EXPORTS
    naki_nal_version
    naki_nal_version_number
    naki_nal_parser_create
    naki_nal_parser_free
    naki_nal_parse
    naki_nal_type_name
    naki_nal_annexb_to_mp4
    naki_nal_mp4_to_annexb
    naki_nal_extract_paramsets
    naki_nal_free_buffers
    naki_nal_find_units
    naki_nal_free_units
EOF

# 链接DLL（静态链接FFmpeg，只导出naki_*符号）
echo "链接 naki_nal.dll..."
gcc -shared -o "${OUTPUT_DIR}/bin/naki_nal.dll" \
    "${PROJECT_ROOT}/build/naki_nal.o" \
    -Wl,--def,"${PROJECT_ROOT}/build/naki_nal.def" \
    -Wl,--out-implib,${OUTPUT_DIR}/lib/naki_nal.lib \
    -Wl,--whole-archive \
    ${FFMPEG_STATIC_DIR}/lib/libavcodec.a \
    ${FFMPEG_STATIC_DIR}/lib/libavutil.a \
    ${FFMPEG_STATIC_DIR}/lib/libswresample.a \
    ${FFMPEG_STATIC_DIR}/lib/libavformat.a \
    -Wl,--no-whole-archive \
    -lws2_32 -lsecur32 -lbcrypt -lole32 -luser32 -lgdi32 -liphlpapi \
    -static-libgcc -static-libstdc++

# 复制头文件
cp "${SRC_DIR}/naki_nal.h" "${OUTPUT_DIR}/include/"

# Strip DLL
strip "${OUTPUT_DIR}/bin/naki_nal.dll"

# 检查输出
echo ""
echo "========================================"
echo "编译完成!"
echo "========================================"
echo "输出目录: ${OUTPUT_DIR}"
echo ""
echo "生成的文件:"
ls -la "${OUTPUT_DIR}/bin/"*.dll 2>/dev/null || echo "  (无 DLL 文件)"
echo ""
echo "检查导出符号 (只应该有 naki_*):"
echo "----------------------------------------"
objdump -p "${OUTPUT_DIR}/bin/naki_nal.dll" | grep "naki_" | head -15
echo "----------------------------------------"
echo ""
echo "Python 调用:"
echo "  import ctypes"
echo "  lib = ctypes.CDLL(r'${OUTPUT_DIR}/bin/naki_nal.dll')"
echo "  print(lib.naki_nal_version())"
