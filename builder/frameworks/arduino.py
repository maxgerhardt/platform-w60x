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
W60X SDK
"""
from os.path import isfile, isdir, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board = env.BoardConfig()

FRAMEWORK_DIR = platform.get_package_dir("framework-arduino-w60x")
assert isdir(FRAMEWORK_DIR)

mcu = env.BoardConfig().get("build.mcu", "")
board_name = env.subst("$BOARD")
upload_protocol = env.subst("$UPLOAD_PROTOCOL")
variant = board.get("build.variant")
variants_dir = (
    join("$PROJECT_DIR", board.get("build.variants_dir"))
    if board.get("build.variants_dir", "")
    else join(FRAMEWORK_DIR, "variants")
)
variant_dir = join(variants_dir, variant)

def process_standard_library_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_STANDARD_LIB" in cpp_defines:
        env['LINKFLAGS'].remove("--specs=nano.specs")
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_PRINTF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_printf_float"])
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_SCANF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_scanf_float"])

def get_arm_math_lib(cpu):
    core = board.get("build.cpu")[7:9]
    if core == "m4":
        return "arm_cortexM4lf_math"
    elif core == "m7":
        return "arm_cortexM7lfsp_math"

    return "arm_cortex%sl_math" % core.upper()

# this core is weird. it doesn't name its library files "libX.a" but just X.a. 
# attempting to link it with the LIBS=.. option will fail. we have to do 
# special linker flags with the "--whole-archive" thing.
static_lib_files = [
    "oneshot", "wmcmd", "wmcommon", "wmdhcpserver", "wmdnsserver", "wmdriver", "wmhttpclient", "wmlwip", "wmmain", 
    "wmota", "wmntp", "wmping", "wmrtos", "wmssl", "wmweb", "wmwebsocket", "wmsslserver", "libairkiss_log", "wlan", "usermain", 
]
# we need absolute paths
static_lib_files = [join(FRAMEWORK_DIR, "tools","sdk", "lib", file + ".a") for file in static_lib_files]
linker_instruction = "-Wl,--whole-archive," + ",".join(static_lib_files) + ",--no-whole-archive" 

env.Append(
    ASFLAGS=["-x", "assembler-with-cpp", "-mabi=aapcs", "-mthumb-interwork"],

    CFLAGS=[
        "-std=gnu11"
    ],

    CXXFLAGS=[
        "-std=gnu++14",
        "-fno-threadsafe-statics",
        "-fno-rtti",
        "-fno-exceptions",
        "-fno-use-cxa-atexit"
    ],

    CCFLAGS=[
        "-Os",  # optimize for size
        "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        "-mthumb",
        "-mabi=aapcs",
        "-march=armv7-m",
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-fmessage-length=0",
        "-fsigned-char",
        "-Wall",
        "-ggdb3",
#        "-nostdlib",
        "-fabi-version=0",
#        "-fno-builtin",
        "--param", "max-inline-insns-single=500"
    ],

    CPPDEFINES=[
        ("GCC_COMPILE", 1),
        "_SYS_ERRNO_H_ ",
        "_IN_ADDR_T_DECLARED", # the SDK is written so poorly that it attempts to 
        "__MACHINE_ENDIAN_H__", # redefine standard types. have to ignore compiler-builtins. 
        "_TIMEVAL_DEFINED",
        "__INSIDE_CYGWIN_NET__"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", "w600"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "os"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "driver"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "wifi"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "app"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "net"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "platform"),
        join(FRAMEWORK_DIR, "tools", "sdk", "include", "lwip2.0.3", "include"),
        variant_dir
    ],

    LINKFLAGS=[
        "-Os",
        "-mthumb",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        "--specs=nosys.specs",
        "-Wl,--gc-sections,--relax",
        "-Wl,--check-sections",
#        "-Wl,--entry=Reset_Handler",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--defsym=LD_MAX_SIZE=%d" % board.get("upload.maximum_size"),
        "-Wl,--defsym=LD_MAX_DATA_SIZE=%d" % board.get(
            "upload.maximum_ram_size"),
        linker_instruction
    ],

    LIBS=[
        #get_arm_math_lib(env.BoardConfig().get("build.cpu"))
        "c", "m", "gcc", "stdc++"
        # handled by linker-unstruction, see above
#        "oneshot", "wmcmd", "wmcommon", "wmdhcpserver", "wmdnsserver", "wmdriver", "wmhttpclient", "wmlwip", "wmmain", 
#        "wmota", "wmntp", "wmping", "wmrtos", "wmssl", "wmweb", "wmwebsocket", "wmsslserver", "libairkiss_log", "wlan", "usermain", 
    ],

    LIBPATH=[
        join(FRAMEWORK_DIR, "tools", "sdk", "lib")
    ]
)

#
# Linker requires preprocessing with correct RAM|ROM sizes
#

# ignore board buildscript, this arduino core knows only one linker script
env.Replace(LDSCRIPT_PATH=join(FRAMEWORK_DIR, "tools", "sdk", "ld", "link_w600.ld"))

#
# Process configuration flags
#

cpp_defines = env.Flatten(env.get("CPPDEFINES", []))

process_standard_library_configuration(cpp_defines)

# copy CCFLAGS to ASFLAGS (-x assembler-with-cpp mode)
env.Append(ASFLAGS=env.get("CCFLAGS", [])[:])

env.Append(
    LIBSOURCE_DIRS=[
        join(FRAMEWORK_DIR, "libraries")
    ]
)

#
# Target: Build Core Library
#

libs = []

# build core
env.BuildSources(
    join("$BUILD_DIR", "FrameworkArduino"),
    join(FRAMEWORK_DIR, "cores", "w600"))

# build variant folder 
if "build.variant" in env.BoardConfig():
    env.Append(CPPPATH=[variant_dir])
    env.BuildSources(join("$BUILD_DIR", "FrameworkArduinoVariant"), variant_dir)

env.Prepend(LIBS=libs)
