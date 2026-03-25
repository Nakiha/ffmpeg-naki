cmake_minimum_required(VERSION 3.16)

project(NakiNAL
    VERSION 1.0.0
    LANGUAGES C
    DESCRIPTION "NAL analysis library with static FFmpeg linking"
)

include(ExternalProject)

# 选项
option(NAKI_BUILD_PYTHON "Build Python extension" OFF)
option(NAKI_FFMPEG_EXTERNAL "Build FFmpeg as external project" ON)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# FFmpeg 配置
if(NOT FFMPEG_ROOT)
    set(FFMPEG_ROOT "${CMAKE_BINARY_DIR}/ffmpeg")
endif()
set(FFMPEG_INCLUDE_DIR "${FFMPEG_ROOT}/include")
set(FFMPEG_LIB_DIR "${FFMPEG_ROOT}/lib")

# ========================================
# FFmpeg External Project
# ========================================
if(NAKI_FFMPEG_EXTERNAL AND NOT EXISTS "${FFMPEG_LIB_DIR}/libavcodec.a")
    message(STATUS "FFmpeg will be built as external project")

    # FFmpeg 配置参数
    set(FFMPEG_CONFIGURE_ARGS
        --prefix=${FFMPEG_ROOT}
        --enable-gpl
        --enable-version3
        --enable-static
        --disable-shared
        --disable-debug
        --disable-doc
        --disable-ffplay
        --disable-ffprobe
        --disable-ffmpeg
        --disable-w32threads
        --enable-pthreads
        --disable-d3d11va
        --disable-dxva2
        --disable-vaapi
        --disable-vdpau
        --disable-cuda
        --disable-cuda-llvm
        --disable-cuvid
        --disable-nvdec
        --disable-nvenc
        --disable-hwaccels
        --disable-encoders
        --disable-muxers
        --disable-filters
        --disable-devices
        --disable-network
        --arch=x86_64
    )

    if(WIN32)
        list(APPEND FFMPEG_CONFIGURE_ARGS --target-os=mingw64)
    endif()

    ExternalProject_Add(ffmpeg_external
        SOURCE_DIR ${CMAKE_SOURCE_DIR}/ffmpeg
        CONFIGURE_COMMAND <SOURCE_DIR>/configure ${FFMPEG_CONFIGURE_ARGS}
        BUILD_COMMAND make -j4
        INSTALL_COMMAND make install
        BUILD_IN_SOURCE 1
        LOG_CONFIGURE 1
        LOG_BUILD 1
    )

    set(FFMPEG_DEPENDS ffmpeg_external)
else()
    message(STATUS "Using existing FFmpeg at ${FFMPEG_ROOT}")
    set(FFMPEG_DEPENDS "")
endif()

# ========================================
# NakiNAL Library
# ========================================
add_library(naki_nal SHARED
    src/naki_nal.c
)

add_dependencies(naki_nal ${FFMPEG_DEPENDS})

target_include_directories(naki_nal
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src
        ${FFMPEG_INCLUDE_DIR}
)

# FFmpeg 静态库
set(FFMPEG_STATIC_LIBS
    ${FFMPEG_LIB_DIR}/libavcodec.a
    ${FFMPEG_LIB_DIR}/libavutil.a
    ${FFMPEG_LIB_DIR}/libswresample.a
)

# 系统库
if(WIN32)
    set(SYSTEM_LIBS ws2_32 secur32 bcrypt ole32 user32 gdi32 iphlpapi)
else()
    set(SYSTEM_LIBS m pthread)
endif()

target_link_libraries(naki_nal
    PRIVATE
        ${FFMPEG_STATIC_LIBS}
        ${SYSTEM_LIBS}
)

# 编译定义
target_compile_definitions(naki_nal PRIVATE NAKI_NAL_BUILD)

# 隐藏 FFmpeg 符号，只导出 naki_*
if(WIN32)
    set(DEF_FILE "${CMAKE_BINARY_DIR}/naki_nal.def")
    file(WRITE ${DEF_FILE}
"LIBRARY naki_nal
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
")
    set_target_properties(naki_nal PROPERTIES
        LINK_FLAGS "-Wl,--def,${DEF_FILE} -Wl,--exclude-libs,ALL"
    )
else()
    set_target_properties(naki_nal PROPERTIES
        C_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN ON
    )
endif()

# 安装
install(TARGETS naki_nal
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(FILES src/naki_nal.h DESTINATION include)

# ========================================
# 测试
# ========================================
enable_testing()

add_executable(test_nal tests/test_nal.c)
target_link_libraries(test_nal naki_nal)
add_test(NAME test_nal COMMAND test_nal)

# ========================================
# 信息
# ========================================
message(STATUS "")
message(STATUS "NakiNAL v${PROJECT_VERSION}")
message(STATUS "  FFmpeg: ${FFMPEG_ROOT}")
message(STATUS "  Build: ${CMAKE_BUILD_TYPE}")
message(STATUS "")
