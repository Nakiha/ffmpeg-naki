# NakiFFmpeg - Custom FFmpeg Distribution

自定义 FFmpeg 分发版，用于纯软件 NAL 分析，静态链接 FFmpeg 隐藏符号。

## 目录结构

```
NakiFfmpeg/
├── src/                  # 源代码
│   ├── naki_nal.h
│   └── naki_nal.c
├── scripts/              # 编译脚本
│   ├── build_cmake.sh    # CMake 编译 (推荐)
│   └── build_ffmpeg_static.sh
├── cmake/                # CMake 工具链
│   └── ucrt64.cmake
├── tests/                # 测试
├── CMakeLists.txt        # CMake 配置
└── ffmpeg/               # FFmpeg submodule
```

## 快速开始

### 1. 克隆

```bash
git clone --recursive git@github.com:Nakiha/ffmpeg-naki.git
cd ffmpeg-naki
git submodule update --init --recursive
```

### 2. 安装依赖 (MSYS2 UCRT64)

```bash
C:\msys64\ucrt64.exe

pacman -S --needed \
    mingw-w64-ucrt-x86_64-toolchain \
    mingw-w64-ucrt-x86_64-nasm \
    mingw-w64-ucrt-x86_64-pkg-config \
    git make cmake
```

### 3. 编译

**方法一：CMake (推荐)**
```bash
cd scripts
./build_cmake.sh
```

**方法二：手动 CMake**
```bash
mkdir build && cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_TOOLCHAIN_FILE=../cmake/ucrt64.cmake
cmake --build . -j$(nproc)
```

**方法三：使用 MSVC**
```bash
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release
```

### 4. 测试

```bash
python tests/test_naki_nal.py
```

## CMake 选项

| 选项 | 默认 | 说明 |
|-----|------|------|
| `NAKI_BUILD_SHARED` | ON | 编译共享库 |
| `NAKI_BUILD_STATIC` | OFF | 编译静态库 |
| `NAKI_FFMPEG_STATIC` | ON | 静态链接 FFmpeg |
| `FFMPEG_ROOT` | 自动 | FFmpeg 静态库路径 |

```bash
cmake .. -DNAKI_BUILD_STATIC=ON -DFFMPEG_ROOT=/path/to/ffmpeg
```

## 输出

编译完成后：
```
build/
├── ffmpeg-static/        # FFmpeg 静态库
│   ├── lib/libavcodec.a
│   └── include/
└── cmake/
    └── bin/
        └── naki_nal.dll  # NAL 分析库
```

## API

```c
#include <naki_nal.h>

// 创建解析器
NalParser *parser = naki_nal_parser_create(CODEC_H264);

// 解析 NAL
int count = naki_nal_parse(parser, data, size, callback, userdata);

// 释放
naki_nal_parser_free(parser);
```

## Python

```python
from ctypes import CDLL, c_char_p

lib = CDLL(r"build\cmake\bin\naki_nal.dll")
lib.naki_nal_version.restype = c_char_p
print(lib.naki_nal_version())
```
