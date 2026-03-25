cmake_minimum_required(VERSION 3.16)
project(NakiNAL VERSION 1.0.0 LANGUAGES C)

# 选项
option(NAKI_BUILD_SHARED "Build shared library" ON)
option(NAKI_BUILD_STATIC "Build static library" OFF)
option(NAKI_FFMPEG_STATIC "Statically link FFmpeg (recommended)" ON)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 查找 FFmpeg 静态库
if(NOT FFMPEG_ROOT)
    set(FFMPEG_ROOT "${CMAKE_SOURCE_DIR}/build/ffmpeg-static")
endif()

# FFmpeg 静态库路径
set(FFMPEG_LIB_DIR "${FFMPEG_ROOT}/lib")
set(FFMPEG_INCLUDE_DIR "${FFMPEG_ROOT}/include")

# 检查 FFmpeg 是否存在
if(NOT EXISTS "${FFMPEG_LIB_DIR}/libavcodec.a")
    message(STATUS "FFmpeg not found at ${FFMPEG_ROOT}")
    message(STATUS "Run: scripts/build_ffmpeg_static.sh first")
endif()

# FFmpeg 静态库列表
set(FFMPEG_STATIC_LIBS
    ${FFMPEG_LIB_DIR}/libavcodec.a
    ${FFMPEG_LIB_DIR}/libavutil.a
    ${FFMPEG_LIB_DIR}/libswresample.a
    ${FFMPEG_LIB_DIR}/libavformat.a
)

# Windows 系统库
set(SYSTEM_LIBS ws2_32 secur32 bcrypt ole32 user32 gdi32 iphlpapi)

# 源文件
set(NAKI_SOURCES
    src/naki_nal.c
)

# 头文件
set(NAKI_HEADERS
    src/naki_nal.h
)

# 编译定义
add_definitions(-DNAKI_NAL_BUILD)

# 静态库
if(NAKI_BUILD_STATIC)
    add_library(naki_nal_static STATIC ${NAKI_SOURCES})
    target_include_directories(naki_nal_static PUBLIC
        ${CMAKE_SOURCE_DIR}/src
        ${FFMPEG_INCLUDE_DIR}
    )
    set_target_properties(naki_nal_static PROPERTIES
        OUTPUT_NAME naki_nal
        ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_ARCHIVE_OUTPUT_DIRECTORY}
    )
endif()

# 共享库
if(NAKI_BUILD_SHARED)
    add_library(naki_nal SHARED ${NAKI_SOURCES})

    target_include_directories(naki_nal PUBLIC
        ${CMAKE_SOURCE_DIR}/src
        ${FFMPEG_INCLUDE_DIR}
    )

    # 链接 FFmpeg 静态库和系统库
    if(NAKI_FFMPEG_STATIC)
        target_link_libraries(naki_nal PRIVATE
            ${FFMPEG_STATIC_LIBS}
            ${SYSTEM_LIBS}
        )
        # 隐藏 FFmpeg 符号
        set_target_properties(naki_nal PROPERTIES
            LINK_FLAGS "-Wl,--exclude-libs,ALL"
        )
    else()
        # 动态链接 FFmpeg
        find_package(PkgConfig REQUIRED)
        pkg_check_modules(FFMPEG REQUIRED libavcodec libavutil libswresample)
        target_include_directories(naki_nal PRIVATE ${FFMPEG_INCLUDE_DIRS})
        target_link_libraries(naki_nal PRIVATE ${FFMPEG_LIBRARIES})
    endif()

    # 导出符号文件
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
        LINK_FLAGS "-Wl,--def,${DEF_FILE}"
        WINDOWS_EXPORT_ALL_SYMBOLS OFF
    )

    # 安装
    install(TARGETS naki_nal
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib
    )
    install(FILES ${NAKI_HEADERS} DESTINATION include)
endif()

# 打印配置信息
message(STATUS "")
message(STATUS "NakiNAL Configuration:")
message(STATUS "  Version:          ${PROJECT_VERSION}")
message(STATUS "  FFmpeg root:      ${FFMPEG_ROOT}")
message(STATUS "  Build shared:     ${NAKI_BUILD_SHARED}")
message(STATUS "  Build static:     ${NAKI_BUILD_STATIC}")
message(STATUS "  FFmpeg static:    ${NAKI_FFMPEG_STATIC}")
message(STATUS "")
