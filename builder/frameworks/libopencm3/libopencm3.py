# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
libOpenCM3

The libOpenCM3 framework aims to create a free/libre/open-source
firmware library for various ARM Cortex-M0(+)/M3/M4 microcontrollers,
including ST STM32, Ti Tiva and Stellaris, NXP LPC 11xx, 13xx, 15xx,
17xx parts, Atmel SAM3, Energy Micro EFM32 and others.

http://www.libopencm3.org
"""

from __future__ import absolute_import

import re
from os import listdir, sep, walk
from os.path import isdir, isfile, join, normpath

from SCons.Script import DefaultEnvironment

from platformio.util import exec_command

env = DefaultEnvironment()
board = env.BoardConfig()

env.SConscript("../_bare.py")

FRAMEWORK_DIR = env.PioPlatform().get_package_dir("framework-libopencm3")
assert isdir(FRAMEWORK_DIR)


def find_ldscript(src_dir):
    ldscript = None
    matches = []
    for item in sorted(listdir(src_dir)):
        _path = join(src_dir, item)
        if not isfile(_path) or not item.endswith(".ld"):
            continue
        matches.append(_path)

    if len(matches) == 1:
        ldscript = matches[0]
    elif isfile(join(src_dir, board.get("build.libopencm3.ldscript", ""))):
        ldscript = join(src_dir, board.get("build.libopencm3.ldscript"))

    return ldscript


def generate_nvic_files():
    for root, _, files in walk(join(FRAMEWORK_DIR, "include", "libopencm3")):
        if "irq.json" not in files or isfile(join(root, "nvic.h")):
            continue

        exec_command(
            ["python", join("scripts", "irq2nvic_h"),
             join("." + root.replace(FRAMEWORK_DIR, ""),
                  "irq.json").replace("\\", "/")],
            cwd=FRAMEWORK_DIR
        )


def parse_makefile_data(makefile):
    data = {"includes": [], "objs": [], "vpath": ["./"]}

    with open(makefile) as f:
        content = f.read()

        # fetch "includes"
        re_include = re.compile(r"^include\s+([^\r\n]+)", re.M)
        for match in re_include.finditer(content):
            data['includes'].append(match.group(1))

        # fetch "vpath"s
        re_vpath = re.compile(r"^VPATH\s+\+?=\s+([^\r\n]+)", re.M)
        for match in re_vpath.finditer(content):
            data['vpath'] += match.group(1).split(":")

        # fetch obj files
        objs_match = re.search(
            r"^OBJS\s+\+?=\s+([^\.]+\.o\s*(?:\s+\\s+)?)+", content, re.M)
        assert objs_match
        data['objs'] = re.sub(
            r"(OBJS|[\+=\\\s]+)", "\n", objs_match.group(0)).split()
    return data


def get_source_files(src_dir):
    mkdata = parse_makefile_data(join(src_dir, "Makefile"))

    for include in mkdata['includes']:
        _mkdata = parse_makefile_data(normpath(join(src_dir, include)))
        for key, value in _mkdata.items():
            for v in value:
                if v not in mkdata[key]:
                    mkdata[key].append(v)

    sources = []
    for obj_file in mkdata['objs']:
        src_file = obj_file[:-1] + "c"
        for search_path in mkdata['vpath']:
            src_path = normpath(join(src_dir, search_path, src_file))
            if isfile(src_path):
                sources.append(join("$BUILD_DIR", "FrameworkLibOpenCM3",
                                    src_path.replace(FRAMEWORK_DIR + sep, "")))
                break
    return sources


def merge_ld_scripts(main_ld_file):

    def _include_callback(match):
        included_ld_file = match.group(1)
        # search included ld file in lib directories
        for root, _, files in walk(join(FRAMEWORK_DIR, "lib")):
            if included_ld_file not in files:
                continue
            with open(join(root, included_ld_file)) as fp:
                return fp.read()
        return match.group(0)

    content = ""
    with open(main_ld_file) as f:
        content = f.read()

    incre = re.compile(r"^INCLUDE\s+\"?([^\.]+\.ld)\"?", re.M)
    with open(main_ld_file, "w") as f:
        f.write(incre.sub(_include_callback, content))

#
# Processing ...
#

root_dir = join(FRAMEWORK_DIR, "lib")
if board.get("build.core") == "tivac":
    env.Append(
        CPPDEFINES=["LM4F"]
    )
    root_dir = join(root_dir, "lm4f")
elif board.get("build.mcu").startswith("stm32"):
    root_dir = join(root_dir, "stm32", board.get("build.mcu")[5:7])

env.Append(
    CPPPATH=[
        FRAMEWORK_DIR,
        join(FRAMEWORK_DIR, "include")
    ]
)

if not board.get("build.ldscript", ""):
    ldscript_path = find_ldscript(root_dir)
    if ldscript_path:
        merge_ld_scripts(ldscript_path)
    generate_nvic_files()
    env.Replace(LDSCRIPT_PATH=ldscript_path)

libs = []
env.VariantDir(
    join("$BUILD_DIR", "FrameworkLibOpenCM3"),
    FRAMEWORK_DIR,
    duplicate=False
)
libs.append(env.Library(
    join("$BUILD_DIR", "FrameworkLibOpenCM3"),
    get_source_files(root_dir)
))

env.Append(LIBS=libs)
