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

import sys
from platform import system
from os import makedirs
from os.path import basename, isdir, join, isfile

from SCons.Script import (ARGUMENTS, COMMAND_LINE_TARGETS, AlwaysBuild,
                          Builder, Default, DefaultEnvironment)


env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

env.Replace(
    AR="arm-none-eabi-ar",
    AS="arm-none-eabi-as",
    CC="arm-none-eabi-gcc",
    CXX="arm-none-eabi-g++",
    GDB="arm-none-eabi-gdb",
    OBJCOPY="arm-none-eabi-objcopy",
    RANLIB="arm-none-eabi-ranlib",
    SIZETOOL="arm-none-eabi-size",

    ARFLAGS=["rc"],

    SIZEPROGREGEXP=r"^(?:\.text|\.data|\.rodata|\.text.align|\.ARM.exidx)\s+(\d+).*",
    SIZEDATAREGEXP=r"^(?:\.data|\.bss|\.noinit)\s+(\d+).*",
    SIZECHECKCMD="$SIZETOOL -A -d $SOURCES",
    SIZEPRINTCMD='$SIZETOOL -B -d $SOURCES',

    PROGSUFFIX=".elf"
)

# Allow user to override via pre:script
if env.get("PROGNAME", "program") == "program":
    env.Replace(PROGNAME="firmware")

env.Append(
    BUILDERS=dict(
        ElfToBin=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "binary", # following: flags from original Makefile
                "-S", # strip all 
                "-g", # strip debug info 
                "-x", # Remove all non-global symbols  
                "-X", # Remove any compiler-generated symbols 
                "-R", ".sbss", # remove section and relocation named ".sbss"
                "-R", ".bss", # ..
                "-R" ,".reginfo", 
                "-R .stack",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".bin"
        ),
        ElfToHex=Builder(
            action=env.VerboseAction(" ".join([
                "$OBJCOPY",
                "-O",
                "ihex",
                "-R",
                ".eeprom",
                "$SOURCES",
                "$TARGET"
            ]), "Building $TARGET"),
            suffix=".hex"
        )
    )
)

if not env.get("PIOFRAMEWORK"):
    env.SConscript("frameworks/_bare.py")

#
# Target: Build executable and linkable firmware
#

target_elf = None
target_firm = None
if "nobuild" in COMMAND_LINE_TARGETS:
    target_elf = join("$BUILD_DIR", "${PROGNAME}.elf")
    target_firm = join("$BUILD_DIR", "${PROGNAME}.bin")
else:
    target_elf = env.BuildProgram()
    target_firm = env.ElfToBin(join("$BUILD_DIR", "${PROGNAME}"), target_elf)

AlwaysBuild(env.Alias("nobuild", target_firm))
target_buildprog = env.Alias("buildprog", target_firm, target_firm)

#
# Target: Create compressed images for uplaoding
#
path_wm_tool = platform.get_package_dir("tool-w60x-download") or ""
if path_wm_tool == "": 
    print("ERROR: Failed to find W60x tools!")
    sys.exit(-1)

# for 1MB target
#IMGTYPE=1M
#UPDADDR=90000
#RUNADDR=10100
# for 2MB target
#IMGTYPE=2M
#UPDADDR=100000
#RUNADDR=10100

# detect from the linker script wehter we have a 1MB or 2MB linker script
is_1mb_version = "1mb.ld" in board.get("build.ldscript", "link_w600_1m.ld")

env.Replace(
    WM_IMAGE_TOOL= join(path_wm_tool, "wm_tool"),
    WM_IMAGE_TOOL_FLAGS=[
        "-b", # source binary
        "$SOURCE",
        "-sb", # secboot 
        join(path_wm_tool, "secboot.img"), # is in same folder as tool
        "-fc",
        "compress",
        "-it", # image type
        "1M" if is_1mb_version else "2M",
        "-ua", # upload address
        "90000" if is_1mb_version else "100000",
        "-ra", # run address
        "10100" if is_1mb_version else "10100",
        "-df", # generate debug firmware
        "-o", # output,
        "$BUILD_DIR/wm_w600"
    ],
    WM_IMAGE_CMD="$WM_IMAGE_TOOL $WM_IMAGE_TOOL_FLAGS"
)

imaging_action = env.Alias("imaging", target_firm, env.VerboseAction("$WM_IMAGE_CMD", "Creating images from $SOURCE")) 
# special case for upload: somehow the uploader doesn't trigger the "AlwaysBuild" options.
# it still needs to know that if it wants the wm_w600.fls file, it needs to execute the imaging command
env.Depends(join("$BUILD_DIR", "wm_w600.fls"), imaging_action)
# always build during normal build
AlwaysBuild(imaging_action)

#
# Target: Print binary size
#

target_size = env.Alias(
    "size", target_elf,
    env.VerboseAction("$SIZEPRINTCMD", "Calculating size $SOURCE"))
AlwaysBuild(target_size)

#
# Target: Upload by default .bin file
#

upload_protocol = env.subst("$UPLOAD_PROTOCOL")
debug_tools = board.get("debug.tools", {})
upload_source = target_firm
upload_actions = []

if upload_protocol.startswith("blackmagic"):
    env.Replace(
        UPLOADER="$GDB",
        UPLOADERFLAGS=[
            "-nx",
            "--batch",
            "-ex", "target extended-remote $UPLOAD_PORT",
            "-ex", "monitor %s_scan" %
            ("jtag" if upload_protocol == "blackmagic-jtag" else "swdp"),
            "-ex", "attach 1",
            "-ex", "load",
            "-ex", "compare-sections",
            "-ex", "kill"
        ],
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS $SOURCE"
    )
    upload_source = target_elf
    upload_actions = [
        env.VerboseAction(env.AutodetectUploadPort, "Looking for BlackMagic port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")
    ]

elif upload_protocol.startswith("jlink"):

    def _jlink_cmd_script(env, source):
        build_dir = env.subst("$BUILD_DIR")
        if not isdir(build_dir):
            makedirs(build_dir)
        script_path = join(build_dir, "upload.jlink")
        commands = [
            "h",
            "loadbin %s, %s" % (source, board.get(
                "upload.offset_address", "0x08000000")),
            "r",
            "q"
        ]
        with open(script_path, "w") as fp:
            fp.write("\n".join(commands))
        return script_path

    env.Replace(
        __jlink_cmd_script=_jlink_cmd_script,
        UPLOADER="JLink.exe" if system() == "Windows" else "JLinkExe",
        UPLOADERFLAGS=[
            "-device", board.get("debug", {}).get("jlink_device"),
            "-speed", "4000",
            "-if", ("jtag" if upload_protocol == "jlink-jtag" else "swd"),
            "-autoconnect", "1"
        ],
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, SOURCE)}"'
    )
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]


elif upload_protocol == "serial":
    def __configure_upload_port(env):
        return env.subst("$UPLOAD_PORT")

    # created by image target
    upload_source = join("$BUILD_DIR", "wm_w600.fls")
    env.Replace(
        __configure_upload_port=__configure_upload_port,
        UPLOADER=
            '"%s"' % join(platform.get_package_dir("tool-w60x-download") or "", "wm_tool"),
        UPLOADERFLAGS=[
            "-ds", # download speed
            "$UPLOAD_SPEED",
            "-it", # image type
            "1M" if is_1mb_version else "2M",
            "-ua", # upload address
            "90000" if is_1mb_version else "100000",
            "-ws",  # work speed (non-download)
            "$UPLOAD_SPEED",
            "-rs", # reset method. "none"/"at"/"rts"
            board.get("upload.resetmethod", "none")
        ],
        UPLOADCMD='$UPLOADER -c "${__configure_upload_port(__env__)}" $UPLOADERFLAGS -dl "$SOURCE"'
    )

    upload_actions = [
        env.VerboseAction(env.AutodetectUploadPort, "Looking for upload port..."),
        env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")
    ]

elif upload_protocol in debug_tools:
    openocd_args = [
        "-d%d" % (2 if int(ARGUMENTS.get("PIOVERBOSE", 0)) else 1)
    ]
    openocd_args.extend(
        debug_tools.get(upload_protocol).get("server").get("arguments", []))
    openocd_args.extend([
        "-c" "reset_config none_separate",
        "-c", "program {$BUILD_DIR/wm_w600_dbg.img} 0x8010000 verify reset; shutdown;"# %
        #board.get("upload.offset_address", "")
    ])
    openocd_args = [
        f.replace("$PACKAGE_DIR",
                  platform.get_package_dir("tool-openocd-w60x") or "")
        for f in openocd_args
    ]
    env.Replace(
        UPLOADER="openocd",
        UPLOADERFLAGS=openocd_args,
        UPLOADCMD="$UPLOADER $UPLOADERFLAGS")

    upload_source = join("$BUILD_DIR", "wm_w600_dbg.img")
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

# custom upload tool
elif upload_protocol == "custom":
    upload_actions = [env.VerboseAction("$UPLOADCMD", "Uploading $SOURCE")]

else:
    sys.stderr.write("Warning! Unknown upload protocol %s\n" % upload_protocol)

AlwaysBuild(env.Alias("upload", upload_source, upload_actions))

#
# Information about obsolete method of specifying linker scripts
#

if any("-Wl,-T" in f for f in env.get("LINKFLAGS", [])):
    print("Warning! '-Wl,-T' option for specifying linker scripts is deprecated. "
          "Please use 'board_build.ldscript' option in your 'platformio.ini' file.")

#
# Default targets: Build, create compressed images, print size
#

Default([target_buildprog, imaging_action ,target_size])
