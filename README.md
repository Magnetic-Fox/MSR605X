# MSR605X utility

Python library with additional text user interface to be used as a standalone solution.

## Introduction

This project aims to be the easiest possible, but fail-safe Python solution for HID-type MSR605X magstripe reader/writer device, which might be used as a library or as a standalone program with typical text user interface.

## How it was started

Last time I (finally!) moved to the Linux Mint system (which I really love).
However, I couldn't make official MSRX program run properly under Wine (which was a bit shocking as Wine is a very good solution and MSRX seems to be one of the easiest piece of software to run) and the other MSR-related projects found on the internet just weren't working for me for strange reasons (assertion errors, etc.).
I then decided to start something really simple to be able to read and write ISO cards (at least).
I thought it would probably never work, but when the first operations succeeded, I wanted to go further - that's how `MSR605X` class was written.
And when it was ready to use I started writing `Interactive` class to provide basic text user interface support.

## Dependencies (what is needed to run this code)?

The only additional library that is needed to run this code is `hid` library, which on Linux Mint can be found in APT under the name `python3-hid` (where it is described as "cython3 interface to hidapi").
The `sys` library (which You can find in imports at the top of this code) is here only for user input/output support (interpreter).

## Device permissions

In order to use this solution, You have to have rights to read and write to the USB device.
This is a bit tricky under Linux as You have to carefully find Your device and then create a udev rule file.
Otherwise You'll have to run this code as a root (e.g. use `sudo`), which I do not recommend as it is not a good idea, especially for a long time (and not safe at all).

Here is an example of my `99-msr.rules` file placed in the `/etc/udev/rules.d/` directory:
```
TODO, AS I DON'T HAVE ACCESS TO THIS FILE NOW AND SIMPLY CAN'T REMEMBER ITS CONTENTS...
```

After creating such file, if You don't want to restart Your system, to make this rule work, type in the terminal those two commands:
```console
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Now, if everything finished properly, MSR605X should be available to use without root permissions.

## Quick reference for MSR605X class

### Constants

#### Default values (VID + PID for MSR605X and additionals)
| Name                         | Value    | Description                                                                        |
| ---------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `DEFAULT_VID`                | `0x0801` | default Vendor ID for MSR605X                                                      |
| `DEFAULT_PID`                | `0x0003` | default Product ID for MSR605X                                                     |
| `DEFAULT_RID`                | `0xFF`   | byte-like; default, working Report ID for MSR605X                                  |
| `DEFAULT_TIMEOUT`            | `100`    | default, short timeout for readData method in milliseconds                         |
| `DEFAULT_CONTINUOUS_TIMEOUT` | `1000`   | default, continuous timeout for continuous read in readData method in milliseconds |

#### Typical constants
| Name  | Value  | Description                              |
| ----- | ------ | ---------------------------------------- |
| `ESC` | `0x1B` | byte-like; escape character code         |
| `FS`  | `0x1C` | byte-like; file separator character code |

#### Response constants
| Name             | Value   | Description                              |
| ---------------- | ------- | ---------------------------------------- |
| `NO_DATA`        | `ESC +` | no data response code                    |
| `BAD_DATA`       | `ESC *` | data read error response code            |
| `CMD_OK`         | `ESC 0` | command successful code                  |
| `CMD_FAIL`       | `ESC A` | command fail code                        |
| `COMM_OK`        | `ESC y` | communication OK code                    |
| `SB_RW_OK`       | `0x30`  | status byte - read/write OK              |
| `SB_RW_ERROR`    | `0x31`  | status byte - read/write error           |
| `SB_CMD_ERROR`   | `0x32`  | status byte - command error              |
| `SB_CMD_INVALID` | `0x34`  | status byte - invalid command            |
| `SB_SWIPE_ERROR` | `0x39`  | status byte - card swipe error           |
| `HICO_SET`       | `ESC h` | Hi-Co set response                       |
| `LOCO_SET`       | `ESC l` | Lo-Co set response                       |

#### Data sequence, track and ISO constants
| Name                 | Value      | Description                                                |
| -------------------- | ---------- | ---------------------------------------------------------- |
| `START_SEQUENCE`     | `ESC s`    | data sequence start                                        |
| `END_SEQUENCE_W`     | `? FS`     | data sequence end - for writing                            |
| `END_SEQUENCE`       | `? FS ESC` | data sequence end - helper for reading                     |
| `ISO1_DATA_START`    | `ESC 0x01` | ISO Track 1 - start sequence                               |
| `ISO2_DATA_START`    | `ESC 0x02` | ISO Track 2 - start sequence                               |
| `ISO3_DATA_START`    | `ESC 0x03` | ISO Track 3 - start sequence                               |
| `START_SENTINEL_1`   | `%`        | ISO 7811, track 1 - start sentinel                         |
| `START_SENTINEL_2_3` | `;`        | ISO 7811, track 2 and 3 - start sentinel                   |
| `END_SENTINEL`       | `?`        | ISO 7811, all tracks - end sentinel                        |
| `ISO_TRACK1`         | `1`        | set track 1 constant - for OR-like operations (0b00000001) |
| `ISO_TRACK2`         | `2`        | set track 2 constant - for OR-like operations (0b00000010) |
| `ISO_TRACK3`         | `4`        | set track 3 constant - for OR-like operations (0b00000100) |
| `ISO_TRACK1_210BPI`  | `0xA1`     | track 1 - 210bpi setting byte                              |
| `ISO_TRACK1_75BPI`   | `0xA0`     | track 1 - 75bpi setting byte                               |
| `ISO_TRACK2_210BPI`  | `0xD2`     | track 2 - 210bpi setting byte                              |
| `ISO_TRACK2_75BPI`   | `0x4B`     | track 2 - 75bpi setting byte                               |
| `ISO_TRACK3_210BPI`  | `0xC1`     | track 3 - 210bpi setting byte                              |
| `ISO_TRACK3_75BPI`   | `0xC0`     | track 3 - 75bpi setting byte                               |

#### Command constants
| Name                  | Value       | Description                               |
| --------------------- | ----------- | ----------------------------------------- |
| `CMD_RESET`           | `ESC a`     | reset command                             |
| `CMD_READ`            | `ESC r`     | ISO read command                          |
| `CMD_WRITE`           | `ESC w`     | ISO write command                         |
| `CMD_COMM_TEST`       | `ESC e`     | communication test command                |
| `CMD_ALL_LED_OFF`     | `ESC 0x81`  | all LEDs off command                      |
| `CMD_ALL_LED_ON`      | `ESC 0x82`  | all LEDs on command                       |
| `CMD_GREEN_LED_ON`    | `ESC 0x83`  | green LED on command                      |
| `CMD_YELLOW_LED_ON`   | `ESC 0x84`  | yellow LED on command                     |
| `CMD_RED_LED_ON`      | `ESC 0x85`  | red LED on command                        |
| `CMD_LEAD_ZERO_SET`   | `ESC z`     | leading zeroes setting command            |
| `CMD_LEAD_ZERO_CHECK` | `ESC l`     | leading zeroes gathering command          |
| `CMD_ERASE_CARD`      | `ESC c`     | card erase command                        |
| `CMD_BPI_SELECT`      | `ESC b`     | BPI setting command                       |
| `CMD_READ_RAW`        | `ESC m`     | RAW read command                          |
| `CMD_WRITE_RAW`       | `ESC n`     | RAW write command                         |
| `CMD_GET_MODEL`       | `ESC t`     | device model gathering command            |
| `CMD_GET_FW_VERSION`  | `ESC v`     | device firmware version gathering command |
| `CMD_BPC_SET`         | `ESC o`     | BPC setting command                       |
| `CMD_SET_HICO`        | `ESC x`     | Hi-Co setting command                     |
| `CMD_SET_LOCO`        | `ESC y`     | Lo-Co setting command                     |
| `CMD_GET_COERCIVITY`  | `ESC d`     | coercivity setting gathering command      |
| `FORCE_CMD_MODE`      | `0x00 0xC2` | force command start sequence              |

#### Probably not supported commands in MSR605X
| Name              | Value      | Description         |
| ----------------- | ---------- | ------------------- |
| `CMD_SENSOR_TEST` | `ESC 0x86` | sensor test command |
| `CMD_RAM_TEST`    | `ESC 0x87` | RAM test command    |

### Methods

#### Technical methods:
| Name       | Parameters                                                                | Description                                                          |
| ---------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `__init__` | vendorID, productID, reportID, timeout, continuousTimeout, breakProcedure | the easiest constructor, used to initialize class on object creation |
| `__del__`  | *none*                                                                    | kind of a destructor to close device if forgotten                    |

#### Internal helper methods:
* `toLSB                (msbByte)` - byte from MSB to LSB converter
* `bytesToLSB           (msbBytes)` - byte string from MSB to LSB converter method
* `dataSplit            (data, size)` - full data to data chunks splitter method
* `dataFill             (data, size)` - data chunk to fixed size filler (filling with zeroes)
* `writeData            (data)` - data to device writer method
* `hardWriteData        (data)` - data to device writer method (hard mode - working only with hard reset command)
* `readData             (continuousTimeout)` - data read from device method (with or without continuous timeout; continuous timeout works like a loop with next iterations occurring after short timeout, e.g. 1 second)
* `exportISOData        (-)` - export all tracks ISO data from response from device
* `exportRAWData        (-)` - export all tracks RAW data from response from device
* `prepareISOData       (track1, track2, track3)` - ISO tracks data to data block converter
* `prepareRAWData       (track1, track2, track3)` - RAW tracks data to raw data block converter (with automated byte data to LSB byte data)

#### Initialization methods:
* `setDevice            (vendorID, productID)` - simple vendor ID and product ID setter method
* `setReportID          (reportID)` - simple report ID setter method
* `setTimeout           (timeout)` - simple timeout setter method
* `setContinuousTimeout (continuousTimeout)` - simple continuous timeout setter method
* `setBreakProcedure    (breakProcedure)` - continuous read break procedure address setter method (read about break procedure below)
* `open                 (-)` - device open method
* `close                (-)` - device close method

#### Actual device command control methods:
* `hardReset            (-)` - hard reset method
* `reset                (-)` - soft reset method
* `read                 (-)` - ISO card read method
* `write                (iso1, iso2, iso3)` - ISO card write method (single or even all tracks)
* `communicationTest    (-)` - device communication test method
* `allLedOff            (-)` - all LEDs off method
* `allLedOn             (-)` - all LEDs on method
* `greenLedOn           (-)` - green LED on method
* `yellowLedOn          (-)` - yellow LED on method (which in fact turns on GREEN and yellow LEDs)
* `redLedOn             (-)` - red LED on method (which in fact turns OFF green and yellow LEDs)
* `sensorTest           (-)` - sensor test method (PROBABLY UNSUPPORTED COMMAND IN MSR605X)
* `ramTest              (-)` - RAM test method (PROBABLY UNSUPPORTED COMMAND IN MSR605X)
* `setLeadingZero       (leadZeroTrack1and3, leadZeroTrack2)` - leading zeroes for track 1 & 3 and track 2 setter method
* `checkLeadingZero     (-)` - leading zeroes gathering method
* `eraseCard            (track1, track2, track3)` - card erase method (single or even all tracks)
* `selectBPI            (settingByte)` - bytes per inch setter method (single or even all tracks)
* `readRawData          (-)` - RAW card read method
* `writeRawData         (track1, track2, track3)` - RAW card write method (buggy - see below)
* `getDeviceModel       (-)` - device model gathering method
* `getFirmwareVersion   (-)` - firmware version gathering method
* `setBPC               (track1, track2, track3)` - bits per character setter method
* `setHiCo              (-)` - high coercivity card setter method
* `setLoCo              (-)` - low coercivity card setter method
* `getCoercivitySetting (-)` - coercivity setting gathering method

## Break procedure

A `break procedure` is a simple piece of code which can decide if readData method has to continue its operation or if it has to stop right now.
It might be useful for situations, where external procedure might want to stop waiting for user to swipe the card.

It can be as easy as (let's say 10 stored in `someInformation` means that we have to break):
```python
def breakProcedure:
	global someInformation
	return someInformation == 10
```

## Bugs

Unfortunately, yes. But limited to RAW writing and copying only (as far as I was able to test everything).
For unknown reasons, sending more than two data packets to the MSR605X device makes it reject incomming command (which has to be fragmentarized to be sent as a whole).
This makes writeRawData method partly unusable, when the whole command size exceeds 127 bytes, which of course affect RAW writing and copying a card.
RAW write and card copy works of course, but not for huge amount of data/big cards.

I hope to find out why it behaves like that and to resolve that issue as soon as possible.

## Disclaimer

I've made much effort to provide here working codes with hope they'll be useful and free from any bugs (except for those listed above).
However I can't guarantee anything. The software is provided here "AS IS" and **I take no responsibility for anything. You're using it on Your own risk!**

## License

Free, with respect to the author (me).

Bartłomiej "Magnetic-Fox" Węgrzyn,
April 7, 2026
