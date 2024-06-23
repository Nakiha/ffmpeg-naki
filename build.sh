#!/bin/bash
script_dir=$(cd "$(dirname "$0")" || exit;pwd)

submodules_dir="$script_dir/submodules"
ffmpeg_dir="$submodules_dir/FFmpeg"

pushd "$ffmpeg_dir" || exit
./configure \
--prefix="../../deps" \
--extra-cflags="-static" \
--extra-ldflags="-static" \
--pkg-config-flags="--static" \
--enable-x86asm \
--enable-shared

make -j
make install
popd || exit