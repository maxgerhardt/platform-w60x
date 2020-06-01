# WinnerMicro W60X: development platform for [PlatformIO](http://platformio.org)

# **WORK IN PROGRESS**

W600 is an embedded Wi-Fi SoC chip which is complying with IEEE802.11b/g/n international standard and which supports multi interface, multi protocol. It can be easily applied to smart appliances, smart home, health care, smart toy, wireless audio & video, industrial and other IoT fields. This SoC integrates Cortex-M3 CPU, Flash, RF Transceiver, CMOS PA, BaseBand. It applies multi interfaces such as SPI, UART, GPIO, I2C, PWM, I2S, 7816. It applies multi encryption and decryption protocol such as PRNG/SHA1/MD5/RC4/DES/3DES/AES/CRC/RSA.

* [Home](http://platformio.org/platforms/w60x) (home page in PlatformIO Platform Registry)
* [Documentation](http://docs.platformio.org/page/platforms/w60x.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](http://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](http://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = w60x
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/maxgerhardt/platform-w60x
board = ...
...
```

# Configuration

Please navigate to [documentation](http://docs.platformio.org/page/platforms/w60x.html).
