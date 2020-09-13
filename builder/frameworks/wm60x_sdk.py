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

FRAMEWORK_DIR = platform.get_package_dir("framework-wm60x-sdk")
assert isdir(FRAMEWORK_DIR)

mcu = env.BoardConfig().get("build.mcu", "")
board_name = env.subst("$BOARD")
upload_protocol = env.subst("$UPLOAD_PROTOCOL")

def process_standard_library_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_STANDARD_LIB" in cpp_defines:
        env['LINKFLAGS'].remove("--specs=nano.specs")
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_PRINTF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_printf_float"])
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_SCANF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_scanf_float"])

# choice for LWIP_141 vs lwip2.0.3 is ommited.
# other flags like COST_DOWN / TLS_COST_DOWN, 
# which are present in the original makefiles,
# are not processed in actual code. 

def get_arm_math_lib(cpu):
    core = board.get("build.cpu")[7:9]
    if core == "m4":
        return "arm_cortexM4lf_math"
    elif core == "m7":
        return "arm_cortexM7lfsp_math"

    return "arm_cortex%sl_math" % core.upper()

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
        "-Wall",
        "-nostdlib",
        "-fno-builtin",
        "--param", "max-inline-insns-single=500"
    ],

    CPPDEFINES=[
        ("GCC_COMPILE", 1),
        ("WM_W600", 1),
        ("TLS_OS_FREERTOS", 1), #from RTOS Makefile
        "_IN_ADDR_T_DECLARED", #from toolchain.def
        "__MACHINE_ENDIAN_H__",
        "_TIMEVAL_DEFINED",
        "__INSIDE_CYGWIN_NET__"
    ],

    CPPPATH=[
        join(FRAMEWORK_DIR, "Src", "OS", "RTOS", "include"),
        # referenced in makefile but actually not existing
        #join(FRAMEWORK_DIR, "Src", "Wlan", "Driver"),
        #join(FRAMEWORK_DIR, "Src", "Wlan", "Supplicant"),
        join(FRAMEWORK_DIR, "Platform", "Boot", "gcc"),
        join(FRAMEWORK_DIR, "Platform", "Common", "Params"),
        join(FRAMEWORK_DIR, "Platform", "Common", "Task"),
        join(FRAMEWORK_DIR, "Platform", "Common", "mem"),
        join(FRAMEWORK_DIR, "Platform", "Common", "fwup"),
        join(FRAMEWORK_DIR, "Platform", "Common", "utils"),
        join(FRAMEWORK_DIR, "Platform", "Common", "crypto"),
        join(FRAMEWORK_DIR, "Platform", "Common", "crypto", "symmetric"),
        join(FRAMEWORK_DIR, "Platform", "Common", "crypto", "digest"),
        join(FRAMEWORK_DIR, "Platform", "Common", "crypto", "math"),
        join(FRAMEWORK_DIR, "Platform", "Inc"),
        join(FRAMEWORK_DIR, "Platform", "Sys"),
        join(FRAMEWORK_DIR, "Src", "App", "wm_atcmd"),
        join(FRAMEWORK_DIR, "Src", "App", "matrixssl"),
	    join(FRAMEWORK_DIR, "Src", "App", "libupnp-1.6.19", "ixml", "inc"), 
	    join(FRAMEWORK_DIR, "Src", "App", "libupnp-1.6.19", "upnp" "inc"),
	    join(FRAMEWORK_DIR, "Src", "App", "libupnp-1.6.19", "ixml", "include"),
	    join(FRAMEWORK_DIR, "Src", "App", "libupnp-1.6.19", "threadutil", "include"),
	    join(FRAMEWORK_DIR, "Src", "App", "libupnp-1.6.19", "upnp", "include"),
	    join(FRAMEWORK_DIR, "Src", "App", "gmediarender-0.0.6"),
	    join(FRAMEWORK_DIR, "Src", "App", "web"),
	    join(FRAMEWORK_DIR, "Src", "App", "OTA"),
	    join(FRAMEWORK_DIR, "Src", "App", "cloud"),
	    join(FRAMEWORK_DIR, "Src", "App", "cJSON"),
	    join(FRAMEWORK_DIR, "Src", "App", "ajtcl-15.04.00a", "inc"),
	    join(FRAMEWORK_DIR, "Src", "App", "ajtcl-15.04.00a", "target", "winnermicro"),
	    join(FRAMEWORK_DIR, "Src", "App", "ajtcl-15.04.00a", "external", "sha2"),
	    join(FRAMEWORK_DIR, "Src", "App", "cJSON"),
	    join(FRAMEWORK_DIR, "Src", "App", "cloud"),
	    join(FRAMEWORK_DIR, "Src", "App", "oneshotconfig"),
	    join(FRAMEWORK_DIR, "Src", "App", "dhcpserver"),
	    join(FRAMEWORK_DIR, "Src", "App", "dnsserver"),
	    join(FRAMEWORK_DIR, "Src", "App", "ping"),
	    join(FRAMEWORK_DIR, "Src", "App", "iperf"),
	    join(FRAMEWORK_DIR, "Src", "App", "libcoap", "include"),
	    join(FRAMEWORK_DIR, "Src", "App", "polarssl", "include"),
	    join(FRAMEWORK_DIR, "Src", "App", "mDNS", "mDNSCore"),
	    join(FRAMEWORK_DIR, "Src", "App", "mDNS", "mDNSPosix"),
	    join(FRAMEWORK_DIR, "Src", "App", "mqtt"),
	    join(FRAMEWORK_DIR, "Src", "App", "easylogger", "inc"),
        join(FRAMEWORK_DIR, "Demo"),
        join(FRAMEWORK_DIR, "Include"),
        join(FRAMEWORK_DIR, "Include", "App"),
        join(FRAMEWORK_DIR, "Include", "Net"),
        join(FRAMEWORK_DIR, "Include", "WiFi"),
        join(FRAMEWORK_DIR, "Include", "OS"),
        join(FRAMEWORK_DIR, "Include", "Driver"),
        join(FRAMEWORK_DIR, "Include", "Platform"),
        join(FRAMEWORK_DIR, "Src", "App", "matrixssl", "core"), # special case: includes "list.h" which also exists in Include/
        join(FRAMEWORK_DIR, "Src", "Network", "api2.0.3"),
        join(FRAMEWORK_DIR, "Src", "Network", "lwip2.0.3"), 
        join(FRAMEWORK_DIR, "Src", "Network", "lwip2.0.3", "include"),  
        join(FRAMEWORK_DIR, "Src", "Network", "lwip2.0.3", "include", "arch"),
        join(FRAMEWORK_DIR, "Src", "Network", "lwip2.0.3", "include", "lwip"),
        join(FRAMEWORK_DIR, "Src", "Network", "lwip2.0.3", "include", "netif"),
	    join(FRAMEWORK_DIR, "Src", "App", "libwebsockets-2.1-stable"),
	    join(FRAMEWORK_DIR, "Src", "App", "httpclient"),
	    join(FRAMEWORK_DIR, "Src", "App", "lwm2m-wakaama", "core"),
	    join(FRAMEWORK_DIR, "Src", "App", "lwm2m-wakaama", "core", "er-coap-13"),
	    join(FRAMEWORK_DIR, "Src", "App", "lwm2m-wakaama", "examples", "shared"),
	    join(FRAMEWORK_DIR, "Src", "App", "lwm2m-wakaama", "examples")
    ],

    LINKFLAGS=[
        "-Os",
        "-mthumb",
        "-mcpu=%s" % env.BoardConfig().get("build.cpu"),
        "--specs=nano.specs",
        "-Wl,--gc-sections,--relax",
        "-Wl,--check-sections",
        "-Wl,--entry=Reset_Handler",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--defsym=LD_MAX_SIZE=%d" % board.get("upload.maximum_size"),
        "-Wl,--defsym=LD_MAX_DATA_SIZE=%d" % board.get(
            "upload.maximum_ram_size"),
        "-static",
        "-nostartfiles"
    ],

    LIBS=[
        #get_arm_math_lib(env.BoardConfig().get("build.cpu"))
        "c", "m", "gcc", "stdc++", "wlan", "airkiss_log"
    ],

    LIBPATH=[
        join(FRAMEWORK_DIR, "Lib", "GNU"),
        join(FRAMEWORK_DIR, "Src", "App","oneshotconfig", "lib_gcc")
    ]
)

#
# Linker requires preprocessing with correct RAM|ROM sizes
#

if not board.get("build.ldscript", ""):
    print("Warning! Cannot find linker script for the current target!\n")
    env.Replace(LDSCRIPT_PATH=join("ldscripts", "ldscript.ld"))

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

platform_exclude_dirs = [
    # not-built source files in crypto stuff
    "Common/crypto/digest/md5Matrix.c",
    "Common/crypto/digest/sha1Matrix.c",
    "Common/crypto/digest/sha256Matrix.c",
    "Common/crypto/math/pstm_montgomery_reduce.c",
    "Common/crypto/math/pstm_sqr_comba.c",
    "Common/crypto/math/pstm.c",
    "Common/crypto/symmetric/aesMatrix.c",
    "Common/crypto/symmetric/arc4.c",
    # bootup files for other compilers
    "Boot/armcc",
    "Boot/iccarm",
    # these files #include ALL .c files --> double definitions; ignore them
    "Drivers/wm_driver.c",
    "Common/wm_common.c"
]
platform_exclude_dirs_src_filter = " ".join(["-<" + d + ">" for d in platform_exclude_dirs])

# build startup files
env.BuildSources(
    join("$BUILD_DIR", "SDKPlatformBoot"),
    join(FRAMEWORK_DIR, "Platform"),
    src_filter="+<*> " + platform_exclude_dirs_src_filter)

# build RTOS
env.BuildSources(
    join("$BUILD_DIR", "SDKRTOS"),
    join(FRAMEWORK_DIR, "Src", "OS", "RTOS"),
    src_filter="+<*> -<ports/port_m3.c> -<wm_rtos.c>") #exclude port file meant for other compiler

network_exclude_dirs = [
    "lwip2.0.3.c",
    "lwip2.0.3/apps/*",
    "lwip2.0.3/core/timers.c",
    "lwip2.0.3/netif/ppp/*",
    "lwip2.0.3/netif/lowpan6.c",
    "lwip2.0.3/netif/slipif.c",
    "lwip2.0.3/core/ipv4/ip_frag.c"
]
network_exclude_dirs_src_filter = " ".join(["-<" + d + ">" for d in network_exclude_dirs])

env.BuildSources(
    join("$BUILD_DIR", "SDKNetwork"),
    join(FRAMEWORK_DIR, "Src", "Network"),
    src_filter="+<*> " + network_exclude_dirs_src_filter)

# Built needed App folders

app_exclude_dirs = [
    # excludes for httpclient
    "httpclient/wm_http_compile.c",
    "httpclient/wm_httpclient_if.c",
    # excludes for libwebsockets
    "libwebsockets-2.1-stable/alloc.c",
    "libwebsockets-2.1-stable/daemonize.c",
    "libwebsockets-2.1-stable/extension*",
    "libwebsockets-2.1-stable/extension*", 
    "libwebsockets-2.1-stable/getifaddrs.c",
    "libwebsockets-2.1-stable/http2.c",
    "libwebsockets-2.1-stable/hpack.c",
    "libwebsockets-2.1-stable/lejp.c",
    "libwebsockets-2.1-stable/lejp-conf.c",
    "libwebsockets-2.1-stable/libev.c",
    "libwebsockets-2.1-stable/libuv.c",
    "libwebsockets-2.1-stable/lws-plat-esp8266.c",
    "libwebsockets-2.1-stable/lws-plat-mbed3.c",
    "libwebsockets-2.1-stable/lws-plat-mbed3.cpp",
    "libwebsockets-2.1-stable/lws-plat-unix.c",
    "libwebsockets-2.1-stable/lws-plat-win.c",
    "libwebsockets-2.1-stable/minihuf.c",
    "libwebsockets-2.1-stable/minilex.c",
    "libwebsockets-2.1-stable/rewrite.c",
    "libwebsockets-2.1-stable/server.c",
    "libwebsockets-2.1-stable/server-handshake.c",
    "libwebsockets-2.1-stable/sha-1.c",
    "libwebsockets-2.1-stable/smtp.c",
    "libwebsockets-2.1-stable/ssl-http2.c",
    "libwebsockets-2.1-stable/ssl-server.c",
    # excludes for libcoap
    "libcoap/coap_io.c",
    "libcoap/uri_libcoap.c",
    # excludes for lwm2m-wakaama
    "lwm2m-wakaama/examples/bootstrap_server/*",
    "lwm2m-wakaama/examples/client/*",
    "lwm2m-wakaama/examples/server/*",
    "lwm2m-wakaama/examples/shared/dtlsconnection.c",
    "lwm2m-wakaama/tests/*",
    # excludes for web
    "web/fsdata_ap_config.c",
    "web/fsdata.c",
    # excludes for wm_atmc
    "wm_atcmd/wm_cmd.c", # includes all c files.
    "wm_atcmd/wm_uart_timer.c",
    # excludes for matrixssl
    "matrixssl/wm_matrixssl_compile.c"
]
app_exclude_dirs_src_filter = " ".join(["-<" + d + ">" for d in app_exclude_dirs])

env.BuildSources(
    join("$BUILD_DIR", "SDKApps"),
    join(FRAMEWORK_DIR, "Src", "App"),
    src_filter="+<*> " + app_exclude_dirs_src_filter) 
    

#env.Prepend(LIBS=libs)
