# NakiFFmpeg - Custom FFmpeg Distribution

自定义 FFmpeg 分发版，用于纯软件 NAL 分析，避免与硬件加速版本的 DLL 符号冲突。

## 特性

- **纯软件解码** - 禁用所有硬件加速 (D3D11VA, DXVA2, NVDEC, NVENC, QSV, CUDA)
- **符号前缀** - 使用 `naki_` 前缀避免 DLL 符号冲突
- **NAL 分析** - 专注于 H.264/HEVC/VVC/AV1 码流分析
- **Python 友好** - 提供 Python 绑定模块

## 环境要求

- MSYS2 UCRT64 环境
- Git
- Python 3.14+ (可选，用于 Python 绑定)

## 快速开始

### 1. 克隆仓库

```bash
git clone --recursive git@github.com:Nakiha/ffmpeg-naki.git
cd ffmpeg-naki

# 如果忘记 --recursive，初始化子模块
git submodule update --init --recursive
```

### 2. 安装依赖 (MSYS2 UCRT64)

```bash
# 打开 MSYS2 UCRT64 终端
C:\msys64\ucrt64.exe

# 安装编译工具链
pacman -S --needed \
    mingw-w64-ucrt-x86_64-toolchain \
    mingw-w64-ucrt-x86_64-nasm \
    mingw-w64-ucrt-x86_64-pkg-config \
    git make
```

### 3. 编译

**软件解码版 (推荐，用于 NAL 分析)**:
```bash
cd /d/Code/NakiFfmpeg
./build_naki_soft.sh
```

**硬件加速版 (需要额外配置)**:
```bash
./build_static_ffmpeg.sh      # 基础编译
./build_ffmpeg_hwaccel.sh     # 硬件加速编译
```

### 4. Python 使用

```python
from naki_ffmpeg import NALAnalyzer

# 分析 NAL 单元
analyzer = NALAnalyzer()
with open("video.h264", "rb") as f:
    data = f.read()

nal_units = NALAnalyzer.find_nal_units(data, "h264")
for nal in nal_units:
    print(f"NAL Type: {NALAnalyzer.get_nal_type_name(nal.nal_type)}")
    print(f"  Size: {nal.size} bytes")
    print(f"  Offset: {nal.offset}")
```

## 目录结构

```
NakiFfmpeg/
├── ffmpeg/                    # FFmpeg 源码 (git submodule)
├── ffmpeg-dist-naki/          # NAKI 软件解码版输出
│   ├── bin/
│   │   ├── nakiavcodec.dll    # 重命名的 avcodec
│   │   ├── nakiavformat.dll
│   │   └── nakiavutil.dll
│   ├── include/               # 头文件
│   └── lib/                   # 导入库
├── naki_ffmpeg/               # Python 绑定模块
│   └── __init__.py
├── resource/                  # 测试资源
│   └── video/                 # 测试片源 (Git LFS)
├── build_naki_soft.sh         # NAKI 软件解码编译脚本
├── build_naki_soft.py         # Python 版编译脚本
├── build_static_ffmpeg.sh     # 基础静态编译脚本
├── build_ffmpeg_hwaccel.sh    # 硬件加速编译脚本
└── BUILD_GUIDE.md             # 本文档
```

## 编译脚本对比

| 脚本 | 用途 | 硬件加速 | 输出类型 | 符号前缀 |
|-----|------|---------|---------|---------|
| `build_naki_soft.sh` | NAL 分析 | ❌ 全部禁用 | 共享库 | `naki_` |
| `build_static_ffmpeg.sh` | 通用 | ❌ | 静态 | 无 |
| `build_ffmpeg_hwaccel.sh` | 硬件加速 | ✅ D3D11/DXVA2/NVDEC/NVENC | 静态 | 无 |

## 符号冲突避免

NAKI 版本使用 `naki_` 符号前缀，避免与系统中的其他 FFmpeg 安装冲突:

```c
// 标准 FFmpeg
avcodec_send_packet()

// NAKI FFmpeg
naki_avcodec_send_packet()
```

这允许在同一 Python 进程中同时使用:
- 硬件加速 FFmpeg (如 BtbN/FFmpeg-Builds) 用于视频播放
- NAKI FFmpeg 用于码流分析

## NAL 单元类型参考

### H.264
| Type | 名称 | 说明 |
|------|------|------|
| 1 | Non-IDR Slice | 非 IDR 切片 |
| 5 | IDR Slice | IDR 切片 |
| 6 | SEI | 补充增强信息 |
| 7 | SPS | 序列参数集 |
| 8 | PPS | 图像参数集 |
| 9 | AUD | 访问单元分隔符 |

### HEVC/H.265
| Type | 名称 | 说明 |
|------|------|------|
| 19-20 | IDR | IDR 切片 |
| 21 | CRA | 清洁随机访问 |
| 32 | VPS | 视频参数集 |
| 33 | SPS | 序列参数集 |
| 34 | PPS | 图像参数集 |

## Git LFS

测试视频文件存储在 Git LFS 中:

```bash
# 安装 Git LFS
git lfs install

# 拉取 LFS 文件
git lfs pull
```

## 验证编译

```bash
# 检查 DLL 依赖
objdump -p ffmpeg-dist-naki/bin/nakiavcodec.dll | grep "DLL Name"

# 应该只看到 Windows 系统 DLL
```

## 常见问题

### 符号冲突
如果出现符号冲突错误，确保:
1. 使用 `naki_` 前缀版本的 DLL
2. 检查 Python 进程中加载的 DLL 路径

### 编译失败
1. 确保在 MSYS2 UCRT64 终端中运行
2. 检查依赖是否完整安装
3. 尝试 `--clean` 选项清理后重新编译

### Git LFS 文件未下载
```bash
git lfs install
git lfs pull
```
