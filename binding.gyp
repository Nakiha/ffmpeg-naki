{
  "targets": [{
    "target_name": "ffmpeg_hello",
    "cflags!": [ "-fno-exceptions" ],
    "cflags_cc!": [ "-fno-exceptions" ],
    "defines": [ "NAPI_DISABLE_CPP_EXCEPTIONS" ],
    "include_dirs": [
      "<!@(node -p \"require('node-addon-api').include\")",
      "<(module_root_dir)/deps/include"
    ],
    "libraries": [
      "<(module_root_dir)/deps/bin/avutil.lib"
    ],
    "sources": [
      "hello.cc"
    ]
  }]
}