# NakiFFmpeg

video encoded bitstream analysis library with static FFmpeg linking. No symbol conflicts with hardware-accelerated FFmpeg.

## Build

```bash
# Requirements: CMake, GCC (MinGW on Windows)
cmake -B build -DCMAKE_TOOLCHAIN_FILE=cmake/ucrt64.cmake
cmake --build build -j4
```

## Python

```bash
pip install .
```

```python
from nakiffmpeg import NalParser, CODEC_H264

parser = NalParser(CODEC_H264)
nals = parser.parse(data)
for nal in nals:
    print(f"Type {nal.type}: {nal.size} bytes")
```

## C API

```c
#include <naki_nal.h>

NalParser *parser = naki_nal_parser_create(CODEC_H264);
int count = naki_nal_parse(parser, data, size, callback, NULL);
naki_nal_parser_free(parser);
```

## Structure

```
├── CMakeLists.txt
├── pyproject.toml
├── src/
│   ├── naki_nal.h
│   └── naki_nal.c
├── nakiffmpeg/       # Python package
└── tests/
```
