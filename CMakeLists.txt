cmake_minimum_required(VERSION 3.16)

project(NakiParser
    VERSION 1.0.0
    LANGUAGES C
)

# 选项
option(BUILD_TESTS "Build tests" ON)
option(BUILD_PYTHON "Build Python extension" OFF)

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 源文件
add_library(naki_parser SHARED
    src/naki_parser.c
)

target_include_directories(naki_parser
    PUBLIC ${CMAKE_SOURCE_DIR}/src
)

target_compile_definitions(naki_parser PRIVATE NAKI_PARSER_BUILD)

# Windows: DEF 文件只导出 naki_* 符号
if(WIN32)
    set(DEF_FILE "${CMAKE_BINARY_DIR}/naki_parser.def")
    file(WRITE ${DEF_FILE}
"LIBRARY naki_parser
EXPORTS
    naki_parser_version
    naki_parser_version_number
    naki_parser_create
    naki_parser_free
    naki_parser_parse
    naki_parser_nal_name
    naki_parser_annexb_to_mp4
    naki_parser_mp4_to_annexb
    naki_parser_find_units
    naki_parser_free_units
")
    set_target_properties(naki_parser PROPERTIES
        LINK_FLAGS "-Wl,--def,${DEF_FILE}"
    )
endif()

# 测试
if(BUILD_TESTS)
    enable_testing()
    add_executable(test_parser tests/test_parser.c)
    target_link_libraries(test_parser naki_parser)
    add_test(NAME test_parser COMMAND test_parser)
endif()

# 安装
install(TARGETS naki_parser
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)
install(FILES src/naki_parser.h DESTINATION include)

# 信息
message(STATUS "")
message(STATUS "NakiParser v${PROJECT_VERSION}")
message(STATUS "")
