"""
Setup script for nakiffmpeg.
Builds the C library using CMake before installing.
"""

import os
import sys
import subprocess
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist


class CMakeExtension(Extension):
    def __init__(self, name):
        super().__init__(name, sources=[])


class CMakeBuild(build_ext):
    def run(self):
        # 检查 CMake
        try:
            subprocess.check_call(["cmake", "--version"])
        except OSError:
            raise RuntimeError("CMake must be installed")

        # 构建目录
        build_dir = Path(self.build_temp)
        build_dir.mkdir(parents=True, exist_ok=True)

        # 源码目录
        source_dir = Path(__file__).parent

        # 确定工具链
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={source_dir / 'nakiffmpeg'}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
        ]

        # Windows: 优先使用 UCRT64，否则 MSVC
        if sys.platform == "win32":
            toolchain = source_dir / "cmake" / "ucrt64.cmake"
            if toolchain.exists():
                cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={toolchain}")

            cfg = "Debug" if self.debug else "Release"
            cmake_args.append(f"-DCMAKE_BUILD_TYPE={cfg}")

            # 尝试 MinGW
            try:
                subprocess.run(["gcc", "--version"], capture_output=True)
                cmake_args.extend(["-G", "MinGW Makefiles"])
            except FileNotFoundError:
                # 回退到 MSVC
                pass
        else:
            cfg = "Debug" if self.debug else "Release"
            cmake_args.append(f"-DCMAKE_BUILD_TYPE={cfg}")

        # 配置
        subprocess.check_call(
            ["cmake", str(source_dir)] + cmake_args,
            cwd=build_dir
        )

        # 编译
        build_args = ["--config", cfg] if sys.platform == "win32" else []
        subprocess.check_call(
            ["cmake", "--build", ".", "-j"] + build_args,
            cwd=build_dir
        )


setup(
    ext_modules=[CMakeExtension("nakiffmpeg")],
    cmdclass={"build_ext": CMakeBuild},
)
