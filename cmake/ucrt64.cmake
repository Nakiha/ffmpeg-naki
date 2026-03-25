# CMake toolchain file for MSYS2 UCRT64 (MinGW-w64)
# Usage: cmake -DCMAKE_TOOLCHAIN_FILE=cmake/ucrt64.cmake ..

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

# UCRT64 paths
set(MSYS2_ROOT "C:/msys64")
set(UCRT64_ROOT "${MSYS2_ROOT}/ucrt64")

# Compilers
set(CMAKE_C_COMPILER "${UCRT64_ROOT}/bin/gcc.exe")
set(CMAKE_CXX_COMPILER "${UCRT64_ROOT}/bin/g++.exe")
set(CMAKE_RC_COMPILER "${UCRT64_ROOT}/bin/windres.exe")

# Find programs in UCRT64
set(CMAKE_FIND_ROOT_PATH "${UCRT64_ROOT}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

# pkg-config
set(PKG_CONFIG_EXECUTABLE "${UCRT64_ROOT}/bin/pkg-config.exe")

# Flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O2 -pipe" CACHE STRING "")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O2 -pipe" CACHE STRING "")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -static-libgcc -static-libstdc++" CACHE STRING "")
set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -static-libgcc -static-libstdc++" CACHE STRING "")
