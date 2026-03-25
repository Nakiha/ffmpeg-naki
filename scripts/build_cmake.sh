#!/bin/bash
# ============================================================================
# NakiNAL CMake Build Script
# ============================================================================
#
# 使用 CMake 编译 NAL 库
#
# 使用方法:
#   ./build_cmake.sh [--clean] [--msvc]
#
# 选项:
#   --clean    清理构建目录
#   --msvc     使用 MSVC (默认使用 UCRT64 MinGW)
#
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build/cmake"

# 解析参数
CLEAN_BUILD=false
USE_MSVC=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --msvc)
            USE_MSVC=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "========================================"
echo "NakiNAL CMake Build"
echo "========================================"
echo "项目根目录: ${PROJECT_ROOT}"
echo "构建目录:   ${BUILD_DIR}"
echo ""

# 清理
if [ "$CLEAN_BUILD" = true ]; then
    echo "清理构建目录..."
    rm -rf "${BUILD_DIR}"
fi

# 检查 FFmpeg 静态库
FFMPEG_STATIC="${PROJECT_ROOT}/build/ffmpeg-static"
if [ ! -f "${FFMPEG_STATIC}/lib/libavcodec.a" ]; then
    echo "FFmpeg 静态库不存在，先编译 FFmpeg..."
    "${SCRIPT_DIR}/build_ffmpeg_static.sh"
fi

# 创建构建目录
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# CMake 配置
echo ""
echo "CMake 配置..."

if [ "$USE_MSVC" = true ]; then
    echo "使用 MSVC 工具链..."
    cmake ../.. \
        -G "Visual Studio 17 2022" \
        -A x64 \
        -DNAKI_BUILD_SHARED=ON \
        -DNAKI_BUILD_STATIC=OFF \
        -DNAKI_FFMPEG_STATIC=ON \
        -DFFMPEG_ROOT="${FFMPEG_STATIC}"
else
    echo "使用 UCRT64 MinGW 工具链..."

    # 检查是否在 MSYS2 环境
    if [ -n "$MSYSTEM" ] && [ "$MSYSTEM" = "UCRT64" ]; then
        # 已经在 MSYS2 中，直接使用
        cmake ../.. \
            -G "MinGW Makefiles" \
            -DCMAKE_TOOLCHAIN_FILE="${PROJECT_ROOT}/cmake/ucrt64.cmake" \
            -DNAKI_BUILD_SHARED=ON \
            -DNAKI_BUILD_STATIC=OFF \
            -DNAKI_FFMPEG_STATIC=ON \
            -DFFMPEG_ROOT="${FFMPEG_STATIC}"
    else
        # 在 Windows CMD/PowerShell 中
        cmake ../.. \
            -G "MinGW Makefiles" \
            -DCMAKE_TOOLCHAIN_FILE="${PROJECT_ROOT}/cmake/ucrt64.cmake" \
            -DNAKI_BUILD_SHARED=ON \
            -DNAKI_BUILD_STATIC=OFF \
            -DNAKI_FFMPEG_STATIC=ON \
            -DFFMPEG_ROOT="${FFMPEG_STATIC}"
    fi
fi

# 编译
echo ""
echo "编译..."
cmake --build . --config Release -j$(nproc 2>/dev/null || echo 4)

# 输出
echo ""
echo "========================================"
echo "编译完成!"
echo "========================================"
echo "输出目录: ${BUILD_DIR}/bin"
echo ""
ls -la "${BUILD_DIR}/bin/"*.dll 2>/dev/null || echo "(无 DLL 文件)"
