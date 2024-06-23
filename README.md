my ffmpeg build repo
# how to build
## windows x86_64
### install msys2
this project use msys2-mingw64 to build ffmpeg libs.

you can download and install msys2 through [msys2 offcial page](https://www.msys2.org/)

### config terminal for vscode (optinal)
add msys2-mingw64 into vscode is a convience way to build our native libs.

press `ctrl`+`,` to open setting, search `terminal.integrated.profiles.windows` click `Edit in setting.json`, then edit `terminal.integrated.profiles.windows` like this
~~~json
"terminal.integrated.profiles.windows": {
    // just append the "mingw64" after other terminal config
    "mingw64": {
        "path": "C:\\msys64\\usr\\bin\\bash.exe",
        "args": [
            "--login",
            "-i"
        ],
        "env": {
            "MSYSTEM": "MINGW64",
            "CHERE_INVOKING": "1",
            "MSYS2_PATH_TYPE": "inherit"
        }
    }
}
~~~

### install mingw64 dev tools
~~~shell
# for chinese developer see https://mirrors.tuna.tsinghua.edu.cn/help/msys2/
# sed -i "s#https\?://mirror.msys2.org/#https://mirrors.tuna.tsinghua.edu.cn/msys2/#g" /etc/pacman.d/mirrorlist*
pacman -Syu
pacman -S mingw-w64-x86_64_toolchain
pacman -S base-devel
pacman -S mingw-w64-x86_64-pkg-config
pacman -S mingw-w64-x86_64-zlib
pacman -S mingw-w64-x86_64-nasm
pacman -S mingw-w64-x86_64-cmake
~~~

### compile and install ffmpeg libs
~~~shell
# cd to ffmpeg dir
# eg: cd /d/code/ffmpeg
cd native/submodules/ffmpeg

# enable ffmpeg and ffprobe for funtion check
./configure \
--prefix="../../build/ffmpeg_build" \
--extra-cflags="-static" \
--extra-ldflags="-static" \
--pkg-config-flags="--static" \
--enable-x86asm \
--enable-shared

# notice: make might work not properly in some non-ascii hostname, if errors occurs, changing your hostname to avoid it
make -j
make install
~~~