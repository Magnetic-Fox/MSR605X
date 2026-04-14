# MSR605X Utility

Python library with additional text user interface to be used as
a standalone solution.

## Table of Contents

[Introduction](#introduction)  
[How it was started?](#how-it-was-started)  
[Dependencies (what is needed to run this code?)](#dependencies-what-is-needed-to-run-this-code)  
[Device permissions](#device-permissions)  
[Interpreter](#interpreter)  
[Quick reference for `MSR605X` class](#quick-reference-for-msr605x-class)  
[Break procedure](#break-procedure)  
[Quick reference for `Interactive` class](#quick-reference-for-interactive-class)  
[Known issues](#known-issues)  
[Devices used for testing](#devices-used-for-testing)  
[Disclaimer](#disclaimer)  
[License](#license)

## Introduction

This project aims to be the easiest possible, but fail-safe Python
solution for HID-type MSR605X magstripe reader/writer device,which might
be used as a library or as a standalone program with typical text user
interface.

Maybe the code isn't the cleanest, but I wanted to make it a one-file
solution for ease of use. That's why I decided to write such a detailed
readme file, which might be considered a documentation.

## How it was started?

Last time I (finally!) moved to the Linux Mint system (which I really
love). However, I couldn't make official MSRX program run properly under
Wine (which was a bit shocking as Wine is a very good solution and MSRX
seems to be one of the easiest piece of software to run) and the other
MSR-related projects found on the internet just weren't working for me
for strange reasons (assertion errors, etc.). I then decided to start
something really simple to be able to read and write ISO cards (at
least). I thought it would probably never work, but when the first
operations succeeded, I wanted to go further - that's how `MSR605X`
class was written. And when it was ready to use I started writing
`Interactive` class to provide basic text user interface support.

## Dependencies (what is needed to run this code?)

The only additional library that is needed to run this code is `hid`
library, which on Linux Mint can be found in APT under the name
`python3-hid` (where it is described as "cython3 interface to hidapi").  
The `sys` library (which You can find in imports at the top of this
code) is here only for user input/output support (interpreter).

## Device permissions

In order to use this solution, You have to have rights to read and write
to the USB device. This is a bit tricky under Linux as You have to
carefully find Your device and then create a udev rule file. Otherwise
You'll have to run this code as a root (e.g. use `sudo`), which I do not
recommend as it is not a good idea, especially for a long time (and not
safe at all).

Here is an example of my `99-hid.rules` file placed in the
`/etc/udev/rules.d/` directory:
```console
SUBSYSTEM=="usb", ATTRS{idVendor}=="0801", ATTRS{idProduct}=="0003", MODE="0666"
KERNEL=="hidraw*", ATTRS{idVendor}=="0801", ATTRS{idProduct}=="0003", MODE="0666"
```

I know, it is not the safest option to use 0666 mode, but others simply
didn't work for me (even with `OWNER` and `GROUP` set). Fortunately, I'm
the only user of my computer. ;)

> [!NOTE]
> You can use any valid name for the file. I've used `99-hid.rules`, but
> probably `99-msr.rules` would be good too.

After creating such file, if You don't want to restart Your system, to
make this rules work, type in the terminal those two commands:
```console
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Now, if everything finished properly, MSR605X should be available to use
without root permissions.

## Interpreter

### How to use it?

That's pretty simple - You can use it just like any other console tool.
Just pass any commands and arguments You need. The only difference is
that this tool interprets all passed arguments as a task list, which
means that You can, for example, ask for five reads executed one after
another or even change used device at the runtime.

> [!WARNING]
> If Your arguments are wrong, program just won't run and will display
> help screen.

### Quick reference for interpreter commands

#### Read/write/copy commands

| Command | Arguments                                    | Description              |
| ------- | -------------------------------------------- | ------------------------ |
| `-r`    | *none*                                       | Read card in ISO mode    |
| `-rb`   | *none*                                       | Read card in RAW mode    |
| `-w`    | `track1string [track2string [track3string]]` | Write card in ISO mode   |
| `-wb`   | `track1hexstr [track2hexstr [track3hexstr]]` | Write card in RAW mode * |
| `-c`    | *none*                                       | Copy card in ISO mode    |
| `-cb`   | *none*                                       | Copy card in RAW mode  * |

Legend:
* - command sets 8 bits per character mode

### Questions to answer

#### How to write only third track of a card?

Just pass two empty strings at the beginning and then string for the
third track:  
`./msr605x.py -w "" "" "2026=04=07"`

#### How to set bits per inch for second track only?

Like in the example above, pass empty string to the first track:  
`./msr605x.py -bi "" 210`

> [!CAUTION]
> You must not provide empty string as a last argument as this is
> interpreted as error!  
> **BAD EXAMPLE:** `./msr605x.py -bi "" 210 ""`

#### How to erase only one or two tracks?

This command is interpreted a bit another - You have to pass numbers
indicating which tracks have to be erased, for example:  
`./msr605x.py -e 3`  
OR  
`./msr605x.py -e 3 2`  
OR  
`./msr605x.py -e 2 1 3`

> [!IMPORTANT]
> Order of the numbers is not important, just do not duplicate them as
> this is interpreted as error.  
> **BAD EXAMPLE:** `./msr605x.py -e 2 1 2`

#### How to set leading zeroes or bits per character for one track only?

This is not supported, because MSR605X provides no command for such
usage (or at least MSR605 as I do not have documentation for MSR605X).  
The only way it can be used is to provide all two parameters for leading
zeroes and all three parameters for bits per character setting.

Example of leading zeroes setting:  
`./msr605x.py -z 61 22`

Example of bits per character setting:  
`./msr605x.py -bc 7 5 5`

#### RAM and sensor tests gives ERROR as a result - what's wrong?

These commands are probably unsupported by MSR605X.
I programmed them as they are mentioned in "MSR605 Programmer's Manual",
because maybe there are MSR605X-like magstripe devices that support
those commands (let me know if they work if You have device other than
mine).

#### I'm setting VID, PID and RID properly, but program doesn't run - what's wrong?

You've probably set the device address and report ID to be used for
communication but haven't used any device commands to do actual
communication. As this has no sense it is treated as a parameter error.

> [!TIP]
> If You want to make a communication test of a chosen device, add `-tc`
> at the end of Your command.  
> For example: `./msr605x.py -vid 0x0801 -pid 0x0003 -tc`

#### I want to stress-test your code!

Please type such command:  
`./msr605x.py -l -h -m -f -i0 -i1 -i2 -i3 -i4 -i1 -tc -zs -gc -ts -tr -bc 7 5 5 -bi 210 75 210 -z 61 22 -sr -hr`

> [!NOTE]
> Sensor and RAM tests would probably return errors (they are probably
> unsupported by MSR605X).

## Quick reference for `MSR605X` class

### Constants

#### Default values (VID + PID for MSR605X and additionals)
| Name                         | Value    | Description                                                                        |
| ---------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `DEFAULT_VID`                | `0x0801` | default Vendor ID for MSR605X                                                      |
| `DEFAULT_PID`                | `0x0003` | default Product ID for MSR605X                                                     |
| `DEFAULT_RID`                | `0xFF`   | byte-like; default, working Report ID for MSR605X                                  |
| `DEFAULT_TIMEOUT`            | `100`    | default, short timeout for readData method in milliseconds                         |
| `DEFAULT_CONTINUOUS_TIMEOUT` | `1000`   | default, continuous timeout for continuous read in readData method in milliseconds |

#### ISO 7811 constants
| Name            | Value                                                    | Description                                                                                              |
| --------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `ISO1_ALPHABET` | `{SPACE}#$()-./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^` | ISO 7811, track 1 alphabet; `%` and `?` excluded as they can't be used for data (start and end sentinel) |
| `ISO2_ALPHABET` | `0123456789=`                                            | ISO 7811, track 2 alphabet; `;` and `?` excluded as they can't be used for data (start and end sentinel) |
| `ISO3_ALPHABET` | `0123456789=`                                            | ISO 7811, track 3 alphabet; `;` and `?` excluded as they can't be used for data (start and end sentinel) |
| `ISO1_MAXSIZE`  | `76`                                                     | ISO 7811, maximum data length for track 1                                                                |
| `ISO2_MAXSIZE`  | `37`                                                     | ISO 7811, maximum data length for track 2                                                                |
| `ISO3_MAXSIZE`  | `104`                                                    | ISO 7811, maximum data length for track 3                                                                |

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
| Name                 | Value      | Description                                                  |
| -------------------- | ---------- | ------------------------------------------------------------ |
| `START_SEQUENCE`     | `ESC s`    | data sequence start                                          |
| `END_SEQUENCE_W`     | `? FS`     | data sequence end - for writing                              |
| `END_SEQUENCE`       | `? FS ESC` | data sequence end - helper for reading                       |
| `ISO1_DATA_START`    | `ESC 0x01` | ISO Track 1 - start sequence                                 |
| `ISO2_DATA_START`    | `ESC 0x02` | ISO Track 2 - start sequence                                 |
| `ISO3_DATA_START`    | `ESC 0x03` | ISO Track 3 - start sequence                                 |
| `START_SENTINEL_1`   | `%`        | ISO 7811, track 1 - start sentinel                           |
| `START_SENTINEL_2_3` | `;`        | ISO 7811, track 2 and 3 - start sentinel                     |
| `END_SENTINEL`       | `?`        | ISO 7811, all tracks - end sentinel                          |
| `ISO_TRACK1`         | `1`        | set track 1 constant - for OR-like operations (`0b00000001`) |
| `ISO_TRACK2`         | `2`        | set track 2 constant - for OR-like operations (`0b00000010`) |
| `ISO_TRACK3`         | `4`        | set track 3 constant - for OR-like operations (`0b00000100`) |
| `ISO_TRACK1_210BPI`  | `0xA1`     | track 1 - 210bpi setting byte                                |
| `ISO_TRACK1_75BPI`   | `0xA0`     | track 1 - 75bpi setting byte                                 |
| `ISO_TRACK2_210BPI`  | `0xD2`     | track 2 - 210bpi setting byte                                |
| `ISO_TRACK2_75BPI`   | `0x4B`     | track 2 - 75bpi setting byte                                 |
| `ISO_TRACK3_210BPI`  | `0xC1`     | track 3 - 210bpi setting byte                                |
| `ISO_TRACK3_75BPI`   | `0xC0`     | track 3 - 75bpi setting byte                                 |

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

#### Technical methods
| Name       | Parameters                                                                            | Description                                                                                                                        |
| ---------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `__init__` | `vendorID`, `productID`, `reportID`, `timeout`, `continuousTimeout`, `breakProcedure` | constructor, used to initialize class on object creation (2x `0x0000` - `0xFFFF`, `0x00` - `0xFF`, 2x `int`, `function` or `None`) |
| `__del__`  | *none*                                                                                | destructor, used to close device if forgotten                                                                                      |

#### Internal helper methods
| Name                | Parameters                                                                | Description                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `toLSB`             | `msbByte`                                                                 | byte from MSB to LSB converter (`0` - `255`)                                                                                                                                     |
| `bytesToLSB`        | `msbBytes`                                                                | byte string from MSB to LSB converter method (`byte-like object`)                                                                                                                |
| `dataSplit`         | `data`, `size`                                                            | full data to data chunks splitter method (`byte-like object`, `int`)                                                                                                             |
| `dataFill`          | `data`, `size`                                                            | data chunk to fixed size filler (filling with zeroes) (`byte-like object`, `int`)                                                                                                |
| `dataFramesPrepare` | `data`                                                                    | data frames to be sent to the HID device preparation method                                                                                                                      |
| `writeData`         | `data`                                                                    | data to device writer method (`byte-like object`)                                                                                                                                |
| `hardWriteData`     | `data`                                                                    | data to device writer method (hard mode - working only with hard reset command; `byte-like object`)                                                                              |
| `readData`          | `continuousTimeout`                                                       | data read from device method (with or without continuous timeout; continuous timeout works like a loop with next iterations occurring after short timeout, e.g. 1 second; `int`) |
| `exportISOData`     | *none*                                                                    | export all tracks ISO data from response from device                                                                                                                             |
| `exportRAWData`     | *none*                                                                    | export all tracks RAW data from response from device                                                                                                                             |
| `prepareISOData`    | `track1`, `track2`, `track3`                                              | ISO tracks data to data block converter (`string`s)                                                                                                                              |
| `prepareRAWData`    | `track1`, `track2`, `track3`                                              | RAW tracks data to raw data block converter (with automated byte data to LSB byte data; `byte-like object`s)                                                                     |
| `isValid`           | `alphabet`, `int`, `string`                                               | string validator method (alphabet `string`, maximum data length as `int`, user `string`)                                                                                         |

#### Initialization methods
| Name                   | Parameters              | Description                                                                                           |
| ---------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------- |
| `setDevice`            | `vendorID`, `productID` | simple vendor ID and product ID setter method (2x `0x0000` - `0xFFFF`)                                |
| `setReportID`          | `reportID`              | simple report ID setter method (`0x00` - `0xFF`)                                                      |
| `setTimeout`           | `timeout`               | simple timeout setter method (`int`)                                                                  |
| `setContinuousTimeout` | `continuousTimeout`     | simple continuous timeout setter method (`int`)                                                       |
| `setBreakProcedure`    | `breakProcedure`        | continuous read break procedure address setter method (`procedure`; read about break procedure below) |
| `open`                 | *none*                  | device open method                                                                                    |
| `close`                | *none*                  | device close method                                                                                   |

#### Actual device command control methods
| Name                   | Parameters                             | Description                                                               |
| ---------------------- | -------------------------------------- | ------------------------------------------------------------------------- |
| `hardReset`            | *none*                                 | hard reset method                                                         |
| `reset`                | *none*                                 | soft reset method                                                         |
| `read`                 | *none*                                 | ISO card read method                                                      |
| `write`                | `iso1`, `iso2`, `iso3`                 | ISO card write method (single or even all tracks; `string`s)              |
| `communicationTest`    | *none*                                 | device communication test method                                          |
| `allLedOff`            | *none*                                 | all LEDs off method                                                       |
| `allLedOn`             | *none*                                 | all LEDs on method                                                        |
| `greenLedOn`           | *none*                                 | green LED on method                                                       |
| `yellowLedOn`          | *none*                                 | yellow LED on method (which in fact turns on GREEN and yellow LEDs)       |
| `redLedOn`             | *none*                                 | red LED on method (which in fact turns OFF green and yellow LEDs)         |
| `sensorTest`           | *none*                                 | sensor test method (**PROBABLY UNSUPPORTED COMMAND IN MSR605X**)          |
| `ramTest`              | *none*                                 | RAM test method (**PROBABLY UNSUPPORTED COMMAND IN MSR605X**)             |
| `setLeadingZero`       | `leadZeroTrack1and3`, `leadZeroTrack2` | leading zeroes for track 1 & 3 and track 2 setter method (2x `0` - `255`) |
| `checkLeadingZero`     | *none*                                 | leading zeroes gathering method                                           |
| `eraseCard`            | `track1`, `track2`, `track3`           | card erase method (single or even all tracks; 3x `True`/`False`)          |
| `selectBPI`            | `settingByte`                          | bytes per inch setter method (`byte-like object`)                         |
| `readRawData`          | *none*                                 | RAW card read method                                                      |
| `writeRawData`         | `track1`, `track2`, `track3`           | RAW card write method (`byte-like object`s)                               |
| `getDeviceModel`       | *none*                                 | device model gathering method                                             |
| `getFirmwareVersion`   | *none*                                 | firmware version gathering method                                         |
| `setBPC`               | `track1`, `track2`, `track3`           | bits per character setter method (3x `5` - `8`)                           |
| `setHiCo`              | *none*                                 | high coercivity card setter method                                        |
| `setLoCo`              | *none*                                 | low coercivity card setter method                                         |
| `getCoercivitySetting` | *none*                                 | coercivity setting gathering method                                       |

## Break procedure

A `break procedure` is a simple piece of code which can decide if
readData method has to continue its operation or if it has to stop right
now. It might be useful in situations, where external procedure might
want to stop waiting for user to swipe the card.

It can be as easy as (let's say 10 stored in `someInformation` variable
means that we have to stop):
```python
def breakProcedure:
	global someInformation
	return someInformation == 10
```

## Quick reference for `Interactive` class

### Methods

#### Technical methods
| Name       | Parameters                          | Description                                                                                   |
| ---------- | ----------------------------------- | --------------------------------------------------------------------------------------------- |
| `__init__` | `vendorID`, `productID`, `reportID` | simple constructor to initialize Interactive object (2x `0x0000` - `0xFFFF`, `0x00` - `0xFF`) |
| `__del__`  | *none*                              | simple destructor to close device (if forgotten)                                              |

#### Device control methods
| Name               | Parameters  | Description                                                                                    |
| ------------------ | ----------- | ---------------------------------------------------------------------------------------------- |
| `setVendorID`      | `vendorID`  | vendor ID setter method (executes newDeviceSetting method automatically; `0x0000` - `0xFFFF`)  |
| `setProductID`     | `productID` | product ID setter method (executes newDeviceSetting method automatically; `0x0000` - `0xFFFF`) |
| `setReportID`      | `reportID`  | report ID setter method (`0x00` - `0xFF`)                                                      |
| `open`             | *none*      | device opening method                                                                          |
| `close`            | *none*      | device closing method                                                                          |

#### Internal helper methods
| Name                         | Parameters                  | Description                                                                                                        |
| ---------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `newDeviceSetting`           | `state`                     | device address changing state manipulation method (`True`/`False`)                                                 |
| `toHex`                      | `byte`                      | byte to 2-digit hex value converter method (`0` - `255`)                                                           |
| `bytesToHex`                 | `byteString`                | byte string to 2-digit hex value converter method (`byte-like object`)                                             |
| `hexStringToBytes`           | `inputString`               | 2-digit hex values string to byte object converter method (string formatted like `46 55 52 52 59 ...`)             |
| `isDataOnlySelected`         | `taskList`                  | is silent mode selection present on the task list checker method (e.g. output from the `argumentExtractor` method) |
| `isOnlyDeviceSettingsOnList` | `taskList`                  | is only device address and report ID settings on the task list checker method                                      |

#### Interpreter methods
| Name                 | Parameters | Description                                                                                 |
| -------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| `getIntFromString`   | `string`   | string of most popular types to integer converter method (e.g. `0xFF`, `0b1010` or `0o777`) |
| `checkTaskList`      | `taskList` | task list validator method (e.g. output from the `argumentExtractor` method)                |
| `argumentExtractor`  | `data`     | string array to task list converter method (e.g. `sys.argv`)                                |

#### Text User Interface methods
| Name              | Parameters                          | Description                    |
| ----------------- | ----------------------------------- | ------------------------------ |
| `headerDisplay`   | *none*                              | program header display method  |
| `displayHelp`     | *none*                              | program help display method    |
| `ISOdataPrintOut` | `status`, `data1`, `data2`, `data3` | ISO read data print out method |
| `RAWdataPrintOut` | `status`, `data1`, `data2`, `data3` | RAW read data print out method |
| `interpreter`     | *none*                              | main interpreter method        |

#### MSR605X command wrappers for Text User Interface 
| Name                | Parameters                             | Description                                                                |
| ------------------- | -------------------------------------- | -------------------------------------------------------------------------- |
| `readISO`           | *none*                                 | ISO card read wrapper method                                               |
| `writeISO`          | `track1`, `track2`, `track3`           | ISO card write wrapper method (`string`s)                                  |
| `copyISO`           | *none*                                 | ISO card copy wrapper method                                               |
| `readRAW`           | *none*                                 | RAW card read wrapper method                                               |
| `writeRAW`          | `track1`, `track2`, `track3`           | RAW card write wrapper method (`hexString`s; 8-bit mode only for now)      |
| `copyRAW`           | *none*                                 | RAW card copy wrapper method (8-bit mode only for now)                     |
| `setBPC`            | `track1`, `track2`, `track3`           | bits per character setter wrapper method (`5` - `8`)                       |
| `setBPI`            | `track1`, `track2`, `track3`           | bits per inch setter wrapper method (3x `None`, `75` or `210`)             |
| `setHiCo`           | *none*                                 | Hi-Co mode setter wrapper method                                           |
| `setLoCo`           | *none*                                 | Lo-Co mode setter wrapper method                                           |
| `setLeadingZeroes`  | `leadZeroTrack1and3`, `leadZeroTrack2` | leading zeroes setter wrapper method (2x `0` - `255`)                      |
| `eraseCard`         | `track1`, `track2`, `track3`           | card erase wrapper method (3x `True`/`False`)                              |
| `deviceModel`       | *none*                                 | device model gathering wrapper method                                      |
| `firmwareVersion`   | *none*                                 | device firmware version gathering wrapper method                           |
| `allLEDOff`         | *none*                                 | all LEDs off wrapper method                                                |
| `greenLED`          | *none*                                 | green LED on wrapper method                                                |
| `greenAndYellowLED` | *none*                                 | green and yellow LEDs on (yellowLedOn wrapper) method                      |
| `redLED`            | *none*                                 | red LED on wrapper method                                                  |
| `allLEDOn`          | *none*                                 | all LEDs on wrapper method                                                 |
| `communicationTest` | *none*                                 | communication test wrapper method                                          |
| `getLeadingZeroes`  | *none*                                 | leading zeroes setting gathering wrapper method                            |
| `getCoercivity`     | *none*                                 | coercivity setting wrapper method                                          |
| `sensorTest`        | *none*                                 | sensor test wrapper method (**OPERATION PROBABLY UNSUPPORTED IN MSR605X**) |
| `RAMTest`           | *none*                                 | RAM test wrapper method (**OPERATION PROBABLY UNSUPPORTED IN MSR605X**)    |
| `softReset`         | *none*                                 | soft reset wrapper method                                                  |
| `hardReset`         | *none*                                 | hard reset wrapper method                                                  |

## Known issues

### Card write or erase ends with error

You're probably using Hi-Co card and just connected the MSR605X to the
USB port.

Please note, that MSR605X loves to start in Lo-Co mode. You can check it
by getting coercivity setting straight after connecting the device to
the computer.  
Any write operation (card erase and copy included) will obviously fail
in such setup (Hi-Co card writing in the Lo-Co mode), so You have to
switch to Hi-Co before writing to such card.

> [!TIP]
> You don't have to manually set Hi-Co or Lo-Co mode and then run this
> script again to write or erase card.  
> It is possible to do both in a single run.
>
> See this example: `./msr605x.py -h -w "TEST" "123" "456"`

### Why turning on the yellow LED turns on green too?

That's the way manufacturer created this device. Yellow LED on command
in fact turns on green and yellow and turns off the red one.

### So, the same situation with red LED?

Yup, unfortunately. This command actually turns off green and yellow LED
and turns on the red one.

### Sensor and RAM tests return errors

Those tests are mentioned in the `MSR605 Programmer's Manual`, but seems
unsupported in the MSR605X (always return FAIL). It is unlikely that my
device has problems with memory or sensors as everything works properly.
However I decided to leave those tests in case they would work for
somebody.

## Devices used for testing

I only have one MSR605X device, which announces itself to the system as
`DEFTUN MSR Reader in FS Mode` / `MagTek Magstripe Insert Reader`
(`0801:0003`). It is possible that there are other devices marked as
compatible with MSR605X that won't work with this solution. If You can
test it - please, tell me if anything works or not.

## Disclaimer

I've made much effort to provide here working codes with hope they'll be
useful and free from any bugs. However I can't guarantee anything.

The software is provided here "AS IS" and
**I take no responsibility for anything.**  
**You're using it on Your own risk!**

## License

Free. Please use this code with respect to the author (me).

Bartłomiej "Magnetic-Fox" Węgrzyn,  
April 14, 2026
