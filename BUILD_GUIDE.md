# NakiFFmpeg - Custom FFmpeg Distribution

自定义 FFmpeg 分发版，用于纯软件 NAL 分析，避免与硬件加速版本的 DLL 符号冲突。

## 目录结构

```
NakiFfmpeg/
├── src/                      # 源代码
│   ├── naki_nal.h            # NAL分析库头文件
│   ├── naki_nal.c            # NAL分析库实现
│   └── naki_ffmpeg/          # Python绑定模块
├── scripts/                  # 编译脚本
│   ├── build_naki_nal.sh     # NAL库编译 (推荐)
│   ├── build_naki_soft.sh    # 共享库编译
│   ├── build_static_ffmpeg.sh
│   └── build_ffmpeg_hwaccel.sh
├── tests/                    # 测试脚本
│   ├── test_naki_nal.py
│   └── test_dual_ffmpeg.py
├── patches/                  # 补丁文件
├── resource/                 # 测试资源 (Git LFS)
├── ffmpeg/                   # FFmpeg源码 (submodule)
└── dist/                     # 编译输出
    └── naki-nal/
        ├── bin/naki_nal.dll
        ├── lib/naki_nal.lib
        └── include/naki_nal.h
```

## 特性

- **静态链接FFmpeg** - 完全隐藏FFmpeg符号
- **无符号冲突** - 可与硬件加速版FFmpeg共存
- **单DLL** - 无外部依赖
- **NAL分析** - H.264/HEVC/VVC/AV1 支持

## 快速开始

### 1. 克隆仓库

```bash
git clone --recursive git@github.com:Nakiha/ffmpeg-naki.git
cd ffmpeg-naki

# 如果忘记 --recursive
git submodule update --init --recursive
```

### 2. 安装依赖 (MSYS2 UCRT64)

```bash
# 打开 MSYS2 UCRT64 终端
C:\msys64\ucrt64.exe

pacman -S --needed \
    mingw-w64-ucrt-x86_64-toolchain \
    mingw-w64-ucrt-x86_64-nasm \
    mingw-w64-ucrt-x86_64-pkg-config \
    git make
```

### 3. 编译

```bash
cd /d/Code/NakiFfmpeg/scripts
./build_naki_nal.sh
```

### 4. 测试

```bash
cd /d/Code/NakiFfmpeg
python tests/test_naki_nal.py
```

## API

```c
// 版本信息
const char* naki_nal_version(void);

// 解析器
NalParser* naki_nal_parser_create(NakiCodecType codec);
void naki_nal_parser_free(NalParser *parser);
int naki_nal_parse(NalParser *parser, const uint8_t *data, size_t size,
                   NalCallback callback, void *userdata);

// 简化API
int naki_nal_find_units(const uint8_t *data, size_t size,
                        NakiCodecType codec,
                        NalUnit **nals_out, size_t *count_out);

// 工具函数
const char* naki_nal_type_name(int nal_type, NakiCodecType codec);
int naki_nal_annexb_to_mp4(...);
int naki_nal_mp4_to_annexb(...);
int naki_nal_extract_paramsets(...);
```

## Python 使用

```python
from ctypes import CDLL, c_char_p

lib = CDLL(r"dist\naki-nal\bin\naki_nal.dll")
lib.naki_nal_version.restype = c_char_p
print(lib.naki_nal_version())  # "NakiNAL 1.0.0 (FFmpeg ...)"
```

## Git LFS

```bash
git lfs install
git lfs pull  # 下载测试视频
```

## 编译选项对比

| 脚本 | 输出 | FFmpeg链接 | 符号冲突 |
|-----|------|-----------|---------|
| `build_naki_nal.sh` | 单DLL | 静态 | 无 |
| `build_naki_soft.sh` | 多DLL | 动态 | 可能 |
