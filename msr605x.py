#!/usr/bin/env python3

# Simple MSR605X driver
#
# by Magnetic-Fox, 02-06.04.2026
#
# (C)2026 Bartłomiej "Magnetic-Fox" Węgrzyn


import sys
import hid


# -------------------------------------------------------------------- #
#  MSR605X driver-like class                                           #
# -------------------------------------------------------------------- #

# Main device class
class MSR605X:
	# CONSTANTS
	# Default values (VID + PID for MSR605X and additionals)
	DEFAULT_VID = 0x0801
	DEFAULT_PID = 0x0003
	DEFAULT_RID = b"\xff"
	DEFAULT_TIMEOUT = 100
	DEFAULT_CONTINUOUS_TIMEOUT = 1000
	
	# Command and typical constants
	ESC = b"\x1b"
	FS = b"\x1c"
	
	NO_DATA = ESC + b"+"
	BAD_DATA = ESC + b"*"
	
	START_SEQUENCE = ESC + b"s"
	END_SEQUENCE_W = b"?" + FS
	END_SEQUENCE = END_SEQUENCE_W + ESC
	ISO1_DATA_START = ESC + b"\x01"
	ISO2_DATA_START = ESC + b"\x02"
	ISO3_DATA_START = ESC + b"\x03"
	
	CMD_RESET = ESC + b"a"
	CMD_READ = ESC + b"r"
	CMD_WRITE = ESC + b"w"
	CMD_COMM_TEST = ESC + b"e"
	CMD_ALL_LED_OFF = ESC + b"\x81"
	CMD_ALL_LED_ON = ESC + b"\x82"
	CMD_GREEN_LED_ON = ESC + b"\x83"
	CMD_YELLOW_LED_ON = ESC + b"\x84"
	CMD_RED_LED_ON = ESC + b"\x85"
	
	# probably not supported in MSR605X
	CMD_SENSOR_TEST = ESC + b"\x86"
	CMD_RAM_TEST = ESC + b"\x87"
	# end of probably not supported in MSR605X

	CMD_LEAD_ZERO_SET = ESC + b"z"
	CMD_LEAD_ZERO_CHECK = ESC + b"l"
	CMD_ERASE_CARD = ESC + b"c"
	CMD_BPI_SELECT = ESC + b"b"
	CMD_READ_RAW = ESC + b"m"
	CMD_WRITE_RAW = ESC + b"n"
	CMD_GET_MODEL = ESC + b"t"
	CMD_GET_FW_VERSION = ESC + b"v"
	CMD_BPC_SET = ESC + b"o"
	CMD_SET_HICO = ESC + b"x"
	CMD_SET_LOCO = ESC + b"y"
	CMD_GET_COERCIVITY = ESC + b"d"
	
	FORCE_CMD_MODE = b"\x00\xc2"
	
	ISO_TRACK1 = 1
	ISO_TRACK2 = 2
	ISO_TRACK3 = 4
	
	ISO_TRACK1_210BPI = b"\xa1"
	ISO_TRACK1_75BPI = b"\xa0"
	ISO_TRACK2_210BPI = b"\xd2"
	ISO_TRACK2_75BPI = b"\x4b"
	ISO_TRACK3_210BPI = b"\xc1"
	ISO_TRACK3_75BPI = b"\xc0"
	
	CMD_OK = ESC + b"0"
	CMD_FAIL = ESC + b"A"
	
	SB_RW_OK = b"0"
	SB_RW_ERROR = b"1"
	SB_CMD_ERROR = b"2"
	SB_CMD_INVALID = b"4"
	SB_SWIPE_ERROR = b"9"
	
	COMM_OK = ESC + b"y"
	HICO_SET = ESC + b"h"
	LOCO_SET = ESC + b"l"
	
	START_SENTINEL_1 = "%"
	START_SENTINEL_2_3 = ";"
	END_SENTINEL = "?"
	
	# METHODS
	# Class init and device connection initialization constructor method
	def __init__(self, vendorID = DEFAULT_VID, productID = DEFAULT_PID, reportID = DEFAULT_RID, timeout = DEFAULT_TIMEOUT, continuousTimeout = DEFAULT_CONTINUOUS_TIMEOUT, breakProcedure = None):
		self.vendorID = vendorID
		self.productID = productID
		self.reportID = reportID
		self.timeout = timeout
		self.continuousTimeout = continuousTimeout
		self.breakProcedure = breakProcedure
		self.hidDevice = hid.device()
		self.rawData = b""
		return
		
	# Class destructor (auto closing device, if forgotten)
	def __del__(self):
		self.close()
		return
		
	# Device address set method
	def setDevice(self, vendorID, productID):
		self.vendorID = vendorID
		self.productID = productID
		return
		
	# Report ID set method
	def setReportID(self, reportID):
		self.reportID = reportID
		return
		
	# Timeout method set method
	def setTimeout(self, timeout):
		self.timeout = timeout
		return
		
	# Continuous timeout set method
	def setContinuousTimeout(self, continuousTimeout):
		self.continuousTimeout = continuousTimeout
		return
		
	# Break procedure set method
	def setBreakProcedure(self, breakProcedure):
		self.breakProcedure = breakProcedure
		return
		
	# Device opening method
	def open(self):
		self.hidDevice.open(self.vendorID, self.productID)
		self.hidDevice.set_nonblocking(False)
		return
		
	# Device closing method
	def close(self):
		self.hidDevice.close()
		return
		
	# Helper method to reverse bits in byte
	def toLSB(self, msbByte):
		return int(bin(msbByte + 256)[-8:][::-1], 2).to_bytes()
		
	# Helper method to reverse all bytes
	def bytesToLSB(self, msbBytes):
		tempBytes = b""
		
		for msbByte in msbBytes:
			tempBytes += self.toLSB(msbByte)
			
		return tempBytes
		
	# Helper method to split data to chunks
	def dataSplit(self, data, size):
		return [data[i:i + size] for i in range(0, len(data), size)]
		
	# Helper method to fill data with zeroes
	def dataFill(self, data, size):
		return data + b"\x00" * (size - len(data))
		
	# Write automation method (slicing + sending)
	def writeData(self, data):
		dataChunks = self.dataSplit(data, 64)
		for dataChunk in dataChunks:
			self.hidDevice.write(self.reportID + self.dataFill(dataChunk, 64))
		return
		
	# Hard write automation method (filling + sending)
	def hardWriteData(self, data):
		self.hidDevice.send_feature_report(self.dataFill(data, 65))
		return
		
	# Read automation method (read + concat with timeout)
	def readData(self, continuousTimeout = None):
		self.rawData = b""
		
		if continuousTimeout != None:
			timeout = continuousTimeout
		else:
			timeout = self.timeout
		
		# Try..Except block for Ctrl+C support
		try:
			# Proper support for timeout in the endless loop
			while True:
				if(temp := self.hidDevice.read(64, timeout)[1:]):
					self.rawData += bytes(temp)
					if timeout != self.timeout:
						timeout = self.timeout
				else:
					if self.breakProcedure != None:
						# If break procedure is set and returns True
						if self.breakProcedure():
							# Then hard reset and exit loop
							self.hardReset()
							break
					
					if continuousTimeout == None:
						break
					else:
						if len(self.rawData) > 0:
							break
		
		# On interruption or simply error, hard reset the device
		except:
			self.hardReset()
			
		return

	# Read data export method (ISO 7811 - tracks 1, 2, 3)
	def exportISOData(self):
		# Default values (also returned on error)
		status = b"\x00"
		iso1 = None
		iso2 = None
		iso3 = None
		
		try:
			if self.rawData[0:2] == self.START_SEQUENCE:
				# Get start positions of all data
				iso1pos = self.rawData.find(self.ISO1_DATA_START) + 2
				iso2pos = self.rawData.find(self.ISO2_DATA_START) + 2
				iso3pos = self.rawData.find(self.ISO3_DATA_START) + 2
				endStatusPos = self.rawData.find(self.END_SEQUENCE) + 3
				
				# Get raw ISO data
				iso1 = self.rawData[iso1pos:iso2pos - 2]
				iso2 = self.rawData[iso2pos:iso3pos - 2]
				iso3 = self.rawData[iso3pos:endStatusPos - 3]
				
				# Get status byte
				status = self.rawData[endStatusPos:endStatusPos + 1]

				# ISO 7811 - Track 1
				# Strip start and end sentinels (if they are there)
				if (iso1[0] == ord(self.START_SENTINEL_1)) and (iso1[-1] == ord(self.END_SENTINEL)):
					iso1 = (iso1[1:][:-1]).decode()

				# Return empty byte-string on no data
				elif iso1 == self.NO_DATA:
					iso1 = ""
					
				# Return nothing on bad data
				elif iso1 == self.BAD_DATA:
					iso1 = None
				
				# ISO 7811 - Track 2
				# Strip start and end sentinels (if they are there)	
				if (iso2[0] == ord(self.START_SENTINEL_2_3)) and (iso2[-1] == ord(self.END_SENTINEL)):
					iso2 = (iso2[1:][:-1]).decode()
				
				# Return empty byte-string on no data	
				elif iso2 == self.NO_DATA:
					iso2 = ""
				
				# Return nothing on bad data
				elif iso2 == self.BAD_DATA:
					iso2 = None

				# ISO 7811 - Track 3
				# Strip start and end sentinels (if they are there)
				if (iso3[0] == ord(self.START_SENTINEL_2_3)) and (iso3[-1] == ord(self.END_SENTINEL)):
					iso3 = (iso3[1:][:-1]).decode()
					
				# Return empty byte-string on no data
				elif iso3 == self.NO_DATA:
					iso3 = ""
				
				# Return nothing on bad data
				elif iso3 == self.BAD_DATA:
					iso3 = None
			
		except:
			# Just do nothing and return default values
			pass
		
		return status, iso1, iso2, iso3
		
	# Raw data export method (ISO 7811 - tracks 1, 2, 3)
	def exportRAWData(self):
		# Default values (also returned on error)
		status = b"\x00"
		iso1raw = None
		iso2raw = None
		iso3raw = None
		
		try:
			if self.rawData[0:2] == self.START_SEQUENCE:
				# Get start positions of all data
				iso1pos = self.rawData.find(self.ISO1_DATA_START) + 3
				iso2pos = self.rawData.find(self.ISO2_DATA_START) + 3
				iso3pos = self.rawData.find(self.ISO3_DATA_START) + 3
				endStatusPos = self.rawData.find(self.END_SEQUENCE) + 3
				
				# Get size of all tracks
				iso1size = self.rawData[self.rawData.find(self.ISO1_DATA_START) + 2] - 1
				iso2size = self.rawData[self.rawData.find(self.ISO2_DATA_START) + 2] - 1
				iso3size = self.rawData[self.rawData.find(self.ISO3_DATA_START) + 2] - 1
				
				# Get raw data of all tracks
				iso1raw = self.rawData[iso1pos:iso1pos + iso1size]
				iso2raw = self.rawData[iso2pos:iso2pos + iso2size]
				iso3raw = self.rawData[iso3pos:iso3pos + iso3size]
				
				# Get status byte
				status = self.rawData[endStatusPos:endStatusPos + 1]
				
		except:
			# Just do nothing and return default values
			pass
			
		return status, iso1raw, iso2raw, iso3raw
		
	# Raw string to be written from tracks preparation method
	def prepareISOData(self, track1, track2, track3):
		self.rawData = self.START_SEQUENCE
		
		self.rawData += self.ISO1_DATA_START
		if track1 != None:
			self.rawData += track1.encode()
			
		self.rawData += self.ISO2_DATA_START
		if track2 != None:
			self.rawData += track2.encode()
			
		self.rawData += self.ISO3_DATA_START
		if track3 != None:
			self.rawData += track3.encode()
			
		self.rawData += self.END_SEQUENCE_W
		return
		
	# Raw string to be written from raw tracks data preparation method
	def prepareRAWData(self, track1, track2, track3):
		# Start with start sequence
		self.rawData = self.START_SEQUENCE
		
		# Convert everything to LSB
		if track1 != None:
			track1LSB = self.bytesToLSB(track1)
		else:
			track1LSB = b""
			
		if track2 != None:
			track2LSB = self.bytesToLSB(track2)
		else:
			track2LSB = b""
			
		if track3 != None:
			track3LSB = self.bytesToLSB(track3)
		else:
			track3LSB = b""
		
		# Get all track lengths
		track1Len = len(track1LSB)
		track2Len = len(track2LSB)
		track3Len = len(track3LSB)
		
		# Add all converted data
		self.rawData += self.ISO1_DATA_START + track1Len.to_bytes() + track1LSB
		self.rawData += self.ISO2_DATA_START + track2Len.to_bytes() + track2LSB
		self.rawData += self.ISO3_DATA_START + track3Len.to_bytes() + track3LSB
		
		# Finish with end sequence
		self.rawData += self.END_SEQUENCE_W
		
		return
	
	# MAIN METHODS
	# Hard reset command send method
	def hardReset(self):
		self.hardWriteData(self.FORCE_CMD_MODE + self.CMD_RESET)
		return
		
	# Reset command send method
	def reset(self):
		self.writeData(self.CMD_RESET)
		return
		
	# Read command method (fully automated)
	def read(self):
		self.writeData(self.CMD_READ)
		self.readData(self.continuousTimeout)
		return self.exportISOData()
		
	# Write command method (fully automated):
	def write(self, iso1, iso2, iso3):
		self.prepareISOData(iso1, iso2, iso3)
		self.writeData(self.CMD_WRITE + self.rawData)
		self.readData(self.continuousTimeout)
		if len(self.rawData) >= 2:
			if self.rawData[0:1] == self.ESC:
				return self.rawData[1:2] == self.SB_RW_OK
			else:
				return False
		else:
			return False
	
	# Communication test method
	def communicationTest(self):
		self.writeData(self.CMD_COMM_TEST)
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.COMM_OK
		else:
			return False
	
	# All LEDs off command send method
	def allLedOff(self):
		self.writeData(self.CMD_ALL_LED_OFF)
		return
		
	# All LEDs on command send method
	def allLedOn(self):
		self.writeData(self.CMD_ALL_LED_ON)
		return
		
	# Turn green LED on command send method (in fact, turns on green LED only)
	def greenLedOn(self):
		self.writeData(self.CMD_GREEN_LED_ON)
		return
		
	# Turn yellow LED on command send method (in fact, turns on green and yellow LED simultaneously)
	def yellowLedOn(self):
		self.writeData(self.CMD_YELLOW_LED_ON)
		return

	# Turn red LED on command send method (in fact, turns on red LED only)
	def redLedOn(self):
		self.writeData(self.CMD_RED_LED_ON)
		return
		
	# PROBABLY UNSUPPORTED IN MSR605X: sensor test method
	def sensorTest(self):
		self.writeData(self.CMD_SENSOR_TEST)
		self.readData(self.continuousTimeout)
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
			
	# PROBABLY UNSUPPORTED IN MSR605X: ram test method
	def ramTest(self):
		self.writeData(self.CMD_RAM_TEST)
		self.readData(self.continuousTimeout)
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
		
	# Leading zero set method
	def setLeadingZero(self, leadZeroTrack1and3, leadZeroTrack2):
		self.writeData(self.CMD_LEAD_ZERO_SET + leadZeroTrack1and3.to_bytes() + leadZeroTrack2.to_bytes())
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
		
	# Leading zero check method
	def checkLeadingZero(self):
		self.writeData(self.CMD_LEAD_ZERO_CHECK)
		self.readData()
		if len(self.rawData) >= 3:
			if self.rawData[0].to_bytes() == self.ESC:
				return self.rawData[1], self.rawData[2]
			else:
				return 0, 0
		else:
			return 0, 0
			
	# Card erase method
	def eraseCard(self, track1, track2, track3):
		selectByte = 0
		
		# Condition needed as track 1 always get erased (if selectByte is 0 or 1)
		if (track1 or track2 or track3) == False:
			return True
		
		# Condition needed only if track 2 or 3 is also selected
		if track1:
			selectByte |= self.ISO_TRACK1
			
		# If track 2 has to be erased
		if track2:
			selectByte |= self.ISO_TRACK2
			
		# If track 3 has to be erased
		if track3:
			selectByte |= self.ISO_TRACK3
			
		self.writeData(self.CMD_ERASE_CARD + selectByte.to_bytes())
		self.readData(self.continuousTimeout)
		
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
			
	# BPI select method
	def selectBPI(self, settingByte):
		self.writeData(self.CMD_BPI_SELECT + settingByte)
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
			
	# Raw data read method
	def readRawData(self):
		self.writeData(self.CMD_READ_RAW)
		self.readData(self.continuousTimeout)
		return self.exportRAWData()
		
	# Raw data write method
	def writeRawData(self, track1, track2, track3):
		self.prepareRAWData(track1, track2, track3)
		self.writeData(self.CMD_WRITE_RAW + self.rawData)
		self.readData(self.continuousTimeout)
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False
	
	# Device model get method
	def getDeviceModel(self):
		self.writeData(self.CMD_GET_MODEL)
		self.readData()
		if len(self.rawData) >= 3:
			if (self.rawData[0].to_bytes() == self.ESC) and (self.rawData[2].to_bytes() == b"S"):
				return self.rawData[1].to_bytes().decode()
			else:
				return "?"
		else:
			return "?"
				
	# Firmware version get method
	def getFirmwareVersion(self):
		self.writeData(self.CMD_GET_FW_VERSION)
		self.readData()
		if len(self.rawData) >= 9:
			if self.rawData[0].to_bytes() == self.ESC:
				return self.rawData[1:9].decode()
			else:
				return "?"
		else:
			return "?"
			
	# Bits per character set method
	def setBPC(self, track1, track2, track3):
		self.writeData(self.CMD_BPC_SET + track1.to_bytes() + track2.to_bytes() + track3.to_bytes())
		self.readData()
		if len(self.rawData) >= 5:
			if self.rawData[0:2] == self.CMD_OK:
				return True, self.rawData[2], self.rawData[3], self.rawData[4]
			elif self.rawData[0:2] == self.CMD_FAIL:
				return False, track1, track2, track3
			else:
				return False, track1, track2, track3
		else:
			return False, track1, track2, track3
		
	# Hi-Co set method
	def setHiCo(self):
		self.writeData(self.CMD_SET_HICO)
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False

	# Lo-Co set method
	def setLoCo(self):
		self.writeData(self.CMD_SET_LOCO)
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.CMD_OK
		else:
			return False

	# Get coercivity setting (H - HiCo, L - LoCo, ? - unknown)
	def getCoercivitySetting(self):
		self.writeData(self.CMD_GET_COERCIVITY)
		self.readData()
		if len(self.rawData) >= 2:
			if self.rawData[0:2] == self.HICO_SET:
				return "H"
			elif self.rawData[0:2] == self.LOCO_SET:
				return "L"
			else:
				return "?"
		else:
			return "?"


# -------------------------------------------------------------------- #
#  Text User Interface class                                           #
# -------------------------------------------------------------------- #

# Command Line Utility class
class Interactive:
	# CONSTANTS
	# % and ? excluded as they can't be used for data (start and end sentinel)
	ISO1_ALPHABET = " #$()-./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^"
	
	# ; and ? excluded as they can't be used for data (start and end sentinel)
	ISO2_ALPHABET = "0123456789="
	
	# ; and ? excluded as they can't be used for data (start and end sentinel)
	ISO3_ALPHABET = "0123456789="
	
	# Maximum data length for ISO 7811 tracks
	ISO1_MAXSIZE = 76
	ISO2_MAXSIZE = 37
	ISO3_MAXSIZE = 104
	
	# METHODS
	# Constructor
	def __init__(self, vendorID = 0x0801, productID = 0x0003, reportID = b"\xff"):
		self.vid = vendorID
		self.pid = productID
		self.rid = reportID
		self.oldVID = self.vid
		self.oldPID = self.pid
		self.oldRID = self.rid
		self.dataOnlyMode = False
		self.deviceOpened = False
		self.settingNewDevice = True
		self.MSR = MSR605X(self.vid, self.pid, self.rid)
		return

	# Destructor
	def __del__(self):
		self.close()
		return
		
	# New device setting flag setter method
	def newDeviceSetting(self, state = True):
		self.settingNewDevice = state
		return
	
	# Vendor ID setter method
	def setVendorID(self, vendorID):
		self.newDeviceSetting()
		self.vid = vendorID
		return
		
	# Product ID setter method
	def setProductID(self, productID):
		self.newDeviceSetting()
		self.pid = productID
		return
		
	# Report ID setter method
	def setReportID(self, reportID):
		self.rid = reportID
		return
		
	# Open wrapper
	def open(self):
		if not self.dataOnlyMode:
			print("Opening device at " + "{:04x}".format(self.vid).upper() + ":" + "{:04x}".format(self.pid).upper() + " with report ID = " + "{:02x}".format(self.rid[0]).upper() + "...", end = "")
			sys.stdout.flush()
		
		try:
			self.MSR.setDevice(self.vid, self.pid)
			self.MSR.setReportID(self.rid)
			self.MSR.open()
			self.deviceOpened = True
			if not self.dataOnlyMode:
				print(" OK!")
			return True
		except:
			if not self.dataOnlyMode:
				print(" ERROR!")
			self.deviceOpened = False
			return False
		
	# Close wrapper
	def close(self):
		if self.deviceOpened:
			if not self.dataOnlyMode:
				print("Closing device at " + "{:04x}".format(self.oldVID).upper() + ":" + "{:04x}".format(self.oldPID).upper() + " with report ID = " + "{:02x}".format(self.oldRID[0]).upper() + "...", end = "")
				sys.stdout.flush()
			
			try:
				self.MSR.close()
				self.deviceOpened = False
				if not self.dataOnlyMode:
					print(" OK!")
				return True
			except:
				if not self.dataOnlyMode:
					print(" ERROR!")
				return False
	
	# Check if string is valid
	def isValid(self, alphabet, maxLength, string):
		if len(string) > maxLength:
			return False
		else:
			for char in string:
				if not char in alphabet:
					return False
		return True
		
	# Byte to hex conversion method
	def toHex(self, byte):
		hexVal = hex(byte)[2:].upper()
		
		if byte >= 16:
			return hexVal
		else:
			return "0" + hexVal
			
	# Byte string to hex conversion method
	def bytesToHex(self, byteString):
		output = ""
		
		for byte in byteString:
			output += self.toHex(byte) + " "
			
		return output[:-1]
	
	# String of hex values to bytes variable converter method
	def hexStringToBytes(self, inputString):
		hexByteStrings = inputString.upper().split(" ")
		output = b""
		
		try:
			for hexByteString in hexByteStrings:
				if hexByteString != "":
					output += int(hexByteString, 16).to_bytes()
			return output
		except:
			return None
	
	# Header display method
	def headerDisplay(self):
		if not self.dataOnlyMode:
			print("MSR605X Command Line Utility")
			print("by Magnetic-Fox, April 2026")
			print("")
		return
	
	# Help display method
	def displayHelp(self):
		if not self.dataOnlyMode:
			print("ISO 7811 mode:                              RAW mode (* - sets 8 BPC):")
			print("  -r                 - read card              -rb                - read card")
			print("  -w T1 [T2 [T3]]    - write card             -wb T1 [T2 [T3]]   - write card *")
			print("  -c                 - copy card              -cb                - copy card  *")
			print("")
			print("Bit settings:                               Coercivity:")
			print("  -bc 7 5 5          - bits per char (5-8)    -h                 - use Hi-Co")
			print("  -bi 210 [75 [210]] - bits per inch          -l                 - use Lo-Co")
			print("")
			print("Leading zeroes:                             Other card operations:")
			print("  -z 61 22           - set T1&3 T2 (0-255)    -e 1 [2 [3]]       - erase tracks")
			print("")
			print("Miscellaneous:                              Device status:")
			print("  -m                 - device model           -tc                - comm. test")
			print("  -f                 - firmware version       -zs                - lead zeroes")
			print("  -i<0-4>            - LED control (4: all)   -gc                - coercivity")
			print("  -p                 - data only output       -ts                - sensor test")
			print("  -vid 0x0801        - set vendor ID          -tr                - RAM test")
			print("  -pid 0x0003        - set product ID         -sr                - soft reset")
			print("  -rid 0xFF          - set report ID          -hr                - hard reset")
		return
	
	# ISO 7811 mode read method
	def readISO(self):
		if not self.dataOnlyMode:
			print("ISO read, please swipe a card...", end = "")
			sys.stdout.flush()
		status, data1, data2, data3 = self.MSR.read()
		
		if (data1 == ""):
			data1 = "<no data>"
		elif (data1 == None):
			data1 = "<read error>"
			
		if (data2 == ""):
			data2 = "<no data>"
		elif (data2 == None):
			data2 = "<read error>"
			
		if (data3 == ""):
			data3 = "<no data>"
		elif (data3 == None):
			data3 = "<read error>"
		
		if status == MSR605X.SB_RW_OK:
			if not self.dataOnlyMode:
				print(" OK!")
				print(" *  Track 1: " + data1)
				print(" *  Track 2: " + data2)
				print(" *  Track 3: " + data3)
			else:
				print(data1)
				print(data2)
				print(data3)
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		return
		
	# ISO 7811 mode write method
	def writeISO(self, track1, track2, track3):
		if not self.dataOnlyMode:
			print("ISO write preparation...")
			print(" *  Track 1 data check...", end = "")
			
		try:
			if (track1Error := not self.isValid(self.ISO1_ALPHABET, self.ISO1_MAXSIZE, track1)):
				if not self.dataOnlyMode:
					print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" OK!")
		except:
			if not self.dataOnlyMode:
				print(" ERROR!")
			track1Error = True
			
		if not self.dataOnlyMode:
			print(" *  Track 2 data check...", end = "")
			
		try:
			if (track2Error := not self.isValid(self.ISO2_ALPHABET, self.ISO2_MAXSIZE, track2)):
				if not self.dataOnlyMode:
					print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" OK!")
		except:
			if not self.dataOnlyMode:
				print(" ERROR!")
			track2Error = True

		if not self.dataOnlyMode:
			print(" *  Track 3 data check...", end = "")
			
		try:
			if (track3Error := not self.isValid(self.ISO3_ALPHABET, self.ISO3_MAXSIZE, track3)):
				if not self.dataOnlyMode:
					print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" OK!")
		except:
			if not self.dataOnlyMode:
				print(" ERROR!")
			track3Error = True
		
		if (track1Error or track2Error or track3Error) == False:
			if not self.dataOnlyMode:
				print("ISO write, please swipe a card...", end = "")
				sys.stdout.flush()
			if (len(track1) > 0) or (len(track2) > 0) or (len(track3) > 0):
				if self.MSR.write(track1, track2, track3):
					if not self.dataOnlyMode:
						print(" OK!")
				else:
					if not self.dataOnlyMode:
						print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" NOTHING TO WRITE!")
		else:
			if not self.dataOnlyMode:
				print("ISO write stopped, wrong input data!")
		
		return
	
	# ISO 7811 mode card copy method
	def copyISO(self):
		if not self.dataOnlyMode:
			print("ISO copy, please swipe a source card...", end = "")
			sys.stdout.flush()
		data = self.MSR.read()
		
		if data[0] == MSR605X.SB_RW_OK:
			if not self.dataOnlyMode:
				print(" OK!")
				print("ISO copy, please swipe a target card...", end = "")
				sys.stdout.flush()
			if self.MSR.write(data[1], data[2], data[3]):
				if not self.dataOnlyMode:
					print(" OK!")
					print(" *  ISO card copy finished successfully!")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
			
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			
		return
			
	# RAW mode read method
	def readRAW(self):
		if not self.dataOnlyMode:
			print("RAW read, please swipe a card...", end = "")
			sys.stdout.flush()
		status, data1, data2, data3 = self.MSR.readRawData()
		
		if (data1 == b""):
			data1 = "<no data>"
		elif (data1 == None):
			data1 = "<read error>"
		else:
			data1 = self.bytesToHex(data1)
			
		if (data2 == b""):
			data2 = "<no data>"
		elif (data2 == None):
			data2 = "<read error>"
		else:
			data2 = self.bytesToHex(data2)
			
		if (data3 == b""):
			data3 = "<no data>"
		elif (data3 == None):
			data3 = "<read error>"
		else:
			data3 = self.bytesToHex(data3)
		
		if status == MSR605X.SB_RW_OK:
			if not self.dataOnlyMode:
				print(" OK!")
				print(" *  Track 1: " + data1)
				print(" *  Track 2: " + data2)
				print(" *  Track 3: " + data3)
			else:
				print(data1)
				print(data2)
				print(data3)
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		return
		
	# RAW mode write method
	def writeRAW(self, track1, track2, track3):
		# Otherwise, MSR605X behaves buggy...
		self.setBPC(8, 8, 8)
		
		if not self.dataOnlyMode:
			print("RAW write preparation...")
			print(" *  Track 1 data conversion...", end = "")
			
		try:
			track1Data = self.hexStringToBytes(track1)
			track1Error = False
			if not self.dataOnlyMode:
				print(" OK!")
		except:
			track1Data = b""
			track1Error = True
			if not self.dataOnlyMode:
				print(" ERROR!")
				
		if not self.dataOnlyMode:
			print(" *  Track 2 data conversion...", end = "")
			
		try:
			track2Data = self.hexStringToBytes(track2)
			track2Error = False
			if not self.dataOnlyMode:
				print(" OK!")
		except:
			track2Data = b""
			track2Error = True
			if not self.dataOnlyMode:
				print(" ERROR!")
				
		if not self.dataOnlyMode:
			print(" *  Track 3 data conversion...", end = "")
		try:
			track3Data = self.hexStringToBytes(track3)
			track3Error = False
			if not self.dataOnlyMode:
				print(" OK!")
		except:
			track3Data = b""
			track3Error = True
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		if (track1Error or track2Error or track3Error) == False:
			if not self.dataOnlyMode:
				print("RAW write, please swipe a card...", end = "")
				sys.stdout.flush()
			if (len(track1Data) > 0) or (len(track2Data) > 0) or (len(track3Data) > 0):
				if self.MSR.writeRawData(track1Data, track2Data, track3Data):
					if not self.dataOnlyMode:
						print(" OK!")
				else:
					if not self.dataOnlyMode:
						print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" NOTHING TO WRITE!")
		else:
			if not self.dataOnlyMode:
				print("RAW write stopped, wrong input data!")
		
		return
	
	# RAW mode card copy method
	def copyRAW(self):
		# Otherwise, MSR605X behaves buggy...
		self.setBPC(8, 8, 8)
		
		if not self.dataOnlyMode:
			print("RAW copy, please swipe a source card...", end = "")
			sys.stdout.flush()
		data = self.MSR.readRawData()
		
		if data[0] == MSR605X.SB_RW_OK:
			if not self.dataOnlyMode:
				print(" OK!")
				print("RAW copy, please swipe a target card...", end = "")
				sys.stdout.flush()
			if self.MSR.writeRawData(data[1], data[2], data[3]):
				if not self.dataOnlyMode:
					print(" OK!")
					print(" *  RAW card copy finished successfully!")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
			
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			
		return
			
	# Bits per character set method
	def setBPC(self, track1, track2, track3):
		if not self.dataOnlyMode:
			print("Bits per character setting...", end = "")
			sys.stdout.flush()
		
		if ((track1 >= 1) and (track1 <= 8) and (track2 >= 1) and (track2 <= 8) and (track3 >= 1) and (track3 <= 8)):
			response = self.MSR.setBPC(track1, track2, track3)
			if response[0]:
				if not self.dataOnlyMode:
					print(" OK! (" + str(response[1]) + ", " + str(response[2]) + ", " + str(response[3]) + ")")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		return
	
	# Bits per inch set method
	def setBPI(self, track1, track2, track3):
		if not self.dataOnlyMode:
			print("Bits per inch setting...", end = "")
		if (track1 == None) and (track2 == None) and (track3 == None):
			if not self.dataOnlyMode:
				print(" NOTHING CHANGED!")
		else:
			if not self.dataOnlyMode:
				print("")
		
		if track1 != None:
			if not self.dataOnlyMode:
				print(" *  Track 1: ", end = "")
			sys.stdout.flush()
			if (track1 == 210) or (track1 == 75):
				if (track1 == 210):
					if self.MSR.selectBPI(MSR605X.ISO_TRACK1_210BPI):
						if not self.dataOnlyMode:
							print(" 210 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
				else:
					if self.MSR.selectBPI(MSR605X.ISO_TRACK1_75BPI):
						if not self.dataOnlyMode:
							print(" 75 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
				
		if track2 != None:
			if not self.dataOnlyMode:
				print(" *  Track 2: ", end = "")
			sys.stdout.flush()
			if (track2 == 210) or (track2 == 75):
				if (track2 == 210):
					if self.MSR.selectBPI(MSR605X.ISO_TRACK2_210BPI):
						if not self.dataOnlyMode:
							print(" 210 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
				else:
					if self.MSR.selectBPI(MSR605X.ISO_TRACK2_75BPI):
						if not self.dataOnlyMode:
							print(" 75 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
			
		if track3 != None:
			if not self.dataOnlyMode:
				print(" *  Track 3: ", end = "")
			sys.stdout.flush()
			if (track3 == 210) or (track3 == 75):
				if (track3 == 210):
					if self.MSR.selectBPI(MSR605X.ISO_TRACK3_210BPI):
						if not self.dataOnlyMode:
							print(" 210 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
				else:
					if self.MSR.selectBPI(MSR605X.ISO_TRACK3_75BPI):
						if not self.dataOnlyMode:
							print(" 75 bpi")
					else:
						if not self.dataOnlyMode:
							print(" ERROR!")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
			
		return
	
	# Hi-Co set method
	def setHiCo(self):
		if not self.dataOnlyMode:
			print("Hi-Co setting...", end = "")
			sys.stdout.flush()
		
		if self.MSR.setHiCo():
			if not self.dataOnlyMode:
				print(" OK!")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			
		return
		
	# Lo-Co set method
	def setLoCo(self):
		if not self.dataOnlyMode:
			print("Lo-Co setting...", end = "")
			sys.stdout.flush()
		
		if self.MSR.setLoCo():
			if not self.dataOnlyMode:
				print(" OK!")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		return
		
	# Leading zeroes set method
	def setLeadingZeroes(self, leadZeroTrack1and3, leadZeroTrack2):
		if not self.dataOnlyMode:
			print("Leading zeroes setting...", end = "")
			sys.stdout.flush()
		
		if ((leadZeroTrack1and3 >= 0) and (leadZeroTrack1and3 <= 255)) and ((leadZeroTrack2 >= 0) and (leadZeroTrack2 <= 255)):
			if self.MSR.setLeadingZero(leadZeroTrack1and3, leadZeroTrack2):
				if not self.dataOnlyMode:
					print(" OK! (" + str(leadZeroTrack1and3) + ", " + str(leadZeroTrack2) + ")")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
		
		return
	
	# Track erasing method
	def eraseCard(self, track1, track2, track3):
		if not self.dataOnlyMode:
			print("Card erase, please swipe a card...", end = "")
			sys.stdout.flush()
		
		if (track1 == False) and (track2 == False) and (track3 == False):
			if not self.dataOnlyMode:
				print(" NOTHING ERASED!")
			
		else:
			if self.MSR.eraseCard(track1, track2, track3):
				if not self.dataOnlyMode:
					print(" OK! (", end = "")
				
				if track1:
					if not self.dataOnlyMode:
						print("track 1", end = "")
					
				if (track1 and track2) or (track1 and track3):
					if not self.dataOnlyMode:
						print(", ", end = "")
					
				if track2:
					if not self.dataOnlyMode:
						print("track 2", end = "")
					
				if (track2 and track3):
					if not self.dataOnlyMode:
						print(", ", end = "")
					
				if track3:
					if not self.dataOnlyMode:
						print("track 3", end = "")
					
				if not self.dataOnlyMode:
					print(")")
			else:
				if not self.dataOnlyMode:
					print(" ERROR!")
		
		return
	
	# Device model get method
	def deviceModel(self):
		if not self.dataOnlyMode:
			print("Device model: ", end = "")
			sys.stdout.flush()
		print(self.MSR.getDeviceModel())
		return
		
	# Firmware version get method
	def firmwareVersion(self):
		if not self.dataOnlyMode:
			print("Firmware version: ", end = "")
			sys.stdout.flush()
		print(self.MSR.getFirmwareVersion())
		return
	
	# All LEDs off method
	def allLEDOff(self):
		if not self.dataOnlyMode:
			print("Turning all LEDs off...", end = "")
			sys.stdout.flush()
		self.MSR.allLedOff()
		if not self.dataOnlyMode:
			print(" OK!")
		return
		
	# Green LED on method
	def greenLED(self):
		if not self.dataOnlyMode:
			print("Turning green LED on...", end = "")
			sys.stdout.flush()
		self.MSR.greenLedOn()
		if not self.dataOnlyMode:
			print(" OK!")
		return
		
	# Green and yellow LED on method
	def greenAndYellowLED(self):
		if not self.dataOnlyMode:
			print("Turning green and yellow LED on...", end = "")
			sys.stdout.flush()
		self.MSR.yellowLedOn()
		if not self.dataOnlyMode:
			print(" OK!")
		return
		
	# Red LED on method
	def redLED(self):
		if not self.dataOnlyMode:
			print("Turning red LED on...", end = "")
			sys.stdout.flush()
		self.MSR.redLedOn()
		if not self.dataOnlyMode:
			print(" OK!")
		return
		
	# All LEDs on method
	def allLEDOn(self):
		if not self.dataOnlyMode:
			print("Turning all LEDs on...", end = "")
			sys.stdout.flush()
		self.MSR.allLedOn()
		if not self.dataOnlyMode:
			print(" OK!")
		return
		
	# Communication test method
	def communicationTest(self):
		if not self.dataOnlyMode:
			print("Communication test pending...", end = "")
			sys.stdout.flush()
		if self.MSR.communicationTest():
			if not self.dataOnlyMode:
				print(" OK!")
			else:
				print("1")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			else:
				print("0")
		return
		
	# Leading zeroes setting gathering method
	def getLeadingZeroes(self):
		if not self.dataOnlyMode:
			print("Leading zeroes information gathering...", end = "")
			sys.stdout.flush()
		leadZeroTrack1and3, leadZeroTrack2 = self.MSR.checkLeadingZero()
		if not self.dataOnlyMode:
			print(" OK!")
			print(" *  Track 1 & Track 3: " + str(leadZeroTrack1and3))
			print(" *  Track 2:           " + str(leadZeroTrack2))
		else:
			print(str(leadZeroTrack1and3))
			print(str(leadZeroTrack2))
		return
		
	# Set coercivity gathering method
	def getCoercivity(self):
		if not self.dataOnlyMode:
			print("Coercivity setting gathering...", end = "")
			sys.stdout.flush()
		coercivity = self.MSR.getCoercivitySetting()
		if not self.dataOnlyMode:
			print(" ", end = "")
		if coercivity == "H":
			if not self.dataOnlyMode:
				print("Hi-Co")
			else:
				print("H")
		elif coercivity == "L":
			if not self.dataOnlyMode:
				print("Lo-Co")
			else:
				print("L")
		else:
			if not self.dataOnlyMode:
				print("Unknown")
			else:
				print("?")
		return
		
	# Sensor test method (PROBABLY UNSUPPORTED OPERATION!)
	def sensorTest(self):
		if not self.dataOnlyMode:
			print("Sensor test pending...", end = "")
			sys.stdout.flush()
		if self.MSR.sensorTest():
			if not self.dataOnlyMode:
				print(" OK!")
			else:
				print("1")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			else:
				print("0")
		return
		
	# RAM test method (PROBABLY UNSUPPORTED OPERATION!)
	def RAMTest(self):
		if not self.dataOnlyMode:
			print("RAM test pending...", end = "")
			sys.stdout.flush()
		if self.MSR.ramTest():
			if not self.dataOnlyMode:
				print(" OK!")
			else:
				print("1")
		else:
			if not self.dataOnlyMode:
				print(" ERROR!")
			else:
				print("0")
		return
		
	# Soft reset method
	def softReset(self):
		if not self.dataOnlyMode:
			print("Device reset (soft)...")
		self.MSR.reset()
		return
		
	# Hard reset method
	def hardReset(self):
		if not self.dataOnlyMode:
			print("Device reset (hard)...")
		self.MSR.hardReset()
		return
		
	# Integer value extractor method
	def getIntFromString(self, string):
		try:
			if "0x" in string:
				return int(string, 16)
			elif "0b" in string:
				return int(string, 2)
			elif "0o" in string:
				return int(string, 8)
			else:
				return int(string)
		except:
			return -1
		
	# Task list validator method (I know it should be programmed better way...)
	def checkTaskList(self, taskList):
		try:
			for task in taskList:
				if (task[0].islower()) and (task[0][0] == "-"):
					taskCode = task[0][1:]
					
					# Only command
					if len(task) == 1:
						# Card read - ISO mode
						if taskCode == "r":
							continue
						# Card read - RAW mode
						elif taskCode == "rb":
							continue
						# Card copy - ISO mode
						elif taskCode == "c":
							continue
						# Card copy - RAW mode
						elif taskCode == "cb":
							continue
						# Set HiCo
						elif taskCode == "h":
							continue
						# Set LoCo
						elif taskCode == "l":
							continue
						# Get device model
						elif taskCode == "m":
							continue
						# Get device firmware
						elif taskCode == "f":
							continue
						# Turn off all LEDs
						elif taskCode == "i0":
							continue
						# Turn on green LED
						elif taskCode == "i1":
							continue
						# Turn on green and yellow LED
						elif taskCode == "i2":
							continue
						# Turn on red LED
						elif taskCode == "i3":
							continue
						# Turn on all LEDs
						elif taskCode == "i4":
							continue
						# Data only output
						elif taskCode == "p":
							continue
						# Communication test
						elif taskCode == "tc":
							continue
						# Get leading zeroes setting
						elif taskCode == "zs":
							continue
						# Get coercivity setting
						elif taskCode == "gc":
							continue
						# Sensor test (probably unsupported)
						elif taskCode == "ts":
							continue
						# RAM test (probably unsupported)
						elif taskCode == "tr":
							continue
						# Soft reset
						elif taskCode == "sr":
							continue
						# Hard reset
						elif taskCode == "hr":
							continue
						# Unknown command
						else:
							return False
							
					# Command + 1 parameter
					elif len(task) == 2:
						# Card write - ISO mode (track 1 only)
						if taskCode == "w":
							if (len(task[1]) > 0) and (self.isValid(self.ISO1_ALPHABET, self.ISO1_MAXSIZE, task[1])):
								continue
							else:
								# Wrong input
								return False
						# Card write - RAW mode (track 1 only)
						elif taskCode == "wb":
							if (len(task[1]) > 0) and (self.hexStringToBytes(task[1]) != None):
								continue
							else:
								# Wrong input
								return False
						# Set BPI (track 1 only)
						elif taskCode == "bi":
							if (task[1] == "210") or (task[1] == "75"):
								continue
							else:
								# Wrong input
								return False
						# Card erase (one chosen track only)
						elif taskCode == "e":
							if (task[1] == "1") or (task[1] == "2") or (task[1] == "3"):
								continue
							else:
								# Wrong input
								return False
						# Set vendor ID of the device address
						elif taskCode == "vid":
							if (self.getIntFromString(task[1]) >= 0) and (self.getIntFromString(task[1]) <= 65535):
								continue
							else:
								# Wrong input
								return False
						# Set product ID of the device address
						elif taskCode == "pid":
							if (self.getIntFromString(task[1]) >= 0) and (self.getIntFromString(task[1]) <= 65535):
								continue
							else:
								# Wrong input
								return False
						# Set report ID used to communicate with the device
						elif taskCode == "rid":
							if (self.getIntFromString(task[1]) >= 0) and (self.getIntFromString(task[1]) <= 255):
								continue
							else:
								# Wrong input
								return False
						# Unknown command
						else:
							return False
					
					# Command + 2 parameters
					elif len(task) == 3:
						# Card write - ISO mode (track 1 and 2 only)
						if taskCode == "w":
							if self.isValid(self.ISO1_ALPHABET, self.ISO1_MAXSIZE, task[1]):
								if (len(task[2]) > 0) and (self.isValid(self.ISO2_ALPHABET, self.ISO2_MAXSIZE, task[2])):
									continue
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Card write - RAW mode (track 1 and 2 only)
						elif taskCode == "wb":
							if self.hexStringToBytes(task[1]) != None:
								if (len(task[2]) > 0) and (self.hexStringToBytes(task[2]) != None):
									continue
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Set BPI (track 1 and 2 only)
						elif taskCode == "bi":
							if (task[1] == "") or (task[1] == "210") or (task[1] == "75"):
								if (task[2] == "210") or (task[2] == "75"):
									continue
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Set leading zeroes
						elif taskCode == "z":
							if (int(task[1]) >= 0) and (int(task[1]) <= 255):
								if (int(task[2]) >= 0) and (int(task[2]) <= 255):
									continue
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Card erase (two chosen tracks only)
						elif taskCode == "e":
							if (task[1] == "1") or (task[1] == "2") or (task[1] == "3"):
								if (task[2] == "1") or (task[2] == "2") or (task[2] == "3"):
									if (task[1] == task[2]):
										# Wrong input (tracks doubled)
										return False
									else:
										continue
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Unknown command
						else:
							return False
					
					# Command + 3 parameters
					elif len(task) == 4:
						# Card write - ISO mode (all tracks)
						if taskCode == "w":
							if self.isValid(self.ISO1_ALPHABET, self.ISO1_MAXSIZE, task[1]):
								if self.isValid(self.ISO2_ALPHABET, self.ISO2_MAXSIZE, task[2]):
									if (len(task[3]) > 0) and (self.isValid(self.ISO3_ALPHABET, self.ISO3_MAXSIZE, task[3])):
										continue
									else:
										# Wrong input
										return False
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Card write - RAW mode (all tracks)
						elif taskCode == "wb":
							if self.hexStringToBytes(task[1]) != None:
								if self.hexStringToBytes(task[2]) != None:
									if (len(task[3]) > 0) and (self.hexStringToBytes(task[3]) != None):
										continue
									else:
										# Wrong input
										return False
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Set BPC
						elif taskCode == "bc":
							if (int(task[1]) >= 5) and (int(task[1]) <= 8) and (int(task[2]) >= 5) and (int(task[2]) <= 8) and (int(task[3]) >= 5) and (int(task[3]) <= 8):
								continue
							else:
								return False
						# Set BPI (all tracks)
						elif taskCode == "bi":
							if (task[1] == "") or (task[1] == "210") or (task[1] == "75"):
								if (task[2] == "") or (task[2] == "210") or (task[2] == "75"):
									if (task[3] == "210") or (task[3] == "75"):
										continue
									else:
										# Wrong input
										return False
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Card erase (all tracks)
						elif taskCode == "e":
							if (task[1] == "1") or (task[1] == "2") or (task[1] == "3"):
								if (task[2] == "1") or (task[2] == "2") or (task[2] == "3"):
									if (task[3] == "1") or (task[3] == "2") or (task[3] == "3"):
										if (task[1] == task[2]) or (task[1] == task[3]) or (task[2] == task[3]):
											# Wrong input (tracks doubled)
											return False
										else:
											continue
									else:
										# Wrong input
										return False
								else:
									# Wrong input
									return False
							else:
								# Wrong input
								return False
						# Unknown command
						else:
							return False
					
					# Command + too much parameters
					else:
						return False
				
				# First parameter on task array is not command
				else:
					return False

		# On interpretation error - parameters are wrong
		except:
			return False
		
		# Everything passed - command and parameters correct
		return True
		
	# Argument extractor method (to the task list)
	def argumentExtractor(self, data):
		output = []
		temp = None
		
		# Extract every argument
		for element in data:
			try:
				# If we have a command (only strings starting with minus and lower case)
				if (element.islower()) and (element[0] == "-"):
					# Skip this step on first iteration (when temp is None)
					if temp != None:
						# But otherwise add temporary buffer to output
						output += [temp]
					# Start new temporary buffer
					temp = [element]
				else:
					# Add to temporary buffer
					temp += [element]
				
			except:
				# Skip errors
				pass
				
		# Add everything left in temporary buffer
		if (temp != None) and (len(temp) != 0):
			output += [temp]
			
		if output == []:
			output = None
			
		return output
	
	# Is data only mode selected check method
	def isDataOnlySelected(self, taskList):
		try:
			return self.taskList.index(["-p"]) > -1
		except:
			return False
		
	# Interpreter method
	def interpreter(self):
		# On no arguments
		if len(sys.argv) <= 1:
			self.headerDisplay()
			self.displayHelp()
		# When there are arguments
		else:
			# Extract arguments
			self.taskList = self.argumentExtractor(sys.argv[1:])
			# Check if arguments are correct
			if self.checkTaskList(self.taskList):
				# Check if "silent mode" is to be enabled
				if self.isDataOnlySelected(self.taskList):
					# Delete all occurrences of "-p" command on the list
					while True:
						try:
							self.taskList.pop(self.taskList.index(["-p"]))
						except:
							break
					# Set silent mode
					self.dataOnlyMode = True
				else:
					# Display header when not in silent mode
					self.headerDisplay()
				
				# Execute all tasks from list
				for task in self.taskList:
					taskCode = task[0][1:]
					try:
						# VID, PID and RID changed in preprocessing
						if (taskCode == "vid") or (taskCode == "pid") or (taskCode == "rid"):
							# Vendor ID change command
							if taskCode == "vid":
								self.newDeviceSetting()
								self.oldVID = self.vid
								self.setVendorID(self.getIntFromString(task[1]))
							# Product ID change command
							elif taskCode == "pid":
								self.newDeviceSetting()
								self.oldPID = self.pid
								self.setProductID(self.getIntFromString(task[1]))
							# Report ID change command
							elif taskCode == "rid":
								self.oldRID = self.rid
								self.setReportID(self.getIntFromString(task[1]).to_bytes())
						else:
							# Close and open the device on address change (also on the first iteration)
							if self.settingNewDevice:
								self.newDeviceSetting(False)
								self.close()
								if not self.open():
									# Stop program on open error
									break
							
							# ISO mode card read command
							if taskCode == "r":
								self.readISO()
							# ISO mode card write command
							elif taskCode == "w":
								if len(task) == 2:
									self.writeISO(task[1], "", "")
								elif len(task) == 3:
									self.writeISO(task[1], task[2], "")
								elif len(task) == 4:
									self.writeISO(task[1], task[2], task[3])
							# ISO mode card copy command
							elif taskCode == "c":
								self.copyISO()
							# RAW mode card read command
							elif taskCode == "rb":
								self.readRAW()
							# RAW mode card write command
							elif taskCode == "wb":
								if len(task) == 2:
									self.writeRAW(task[1], "", "")
								elif len(task) == 3:
									self.writeRAW(task[1], task[2], "")
								elif len(task) == 4:
									self.writeRAW(task[1], task[2], task[3])
							# RAW mode card copy command
							elif taskCode == "cb":
								self.copyRAW()
							# Bits per character change command
							elif taskCode == "bc":
								self.setBPC(int(task[1]), int(task[2]), int(task[3]))
							# Bits per inch change command
							elif taskCode == "bi":
								# Get settings from arguments
								try:
									track1BPI = int(task[1])
								except:
									track1BPI = None
								try:
									track2BPI = int(task[2])
								except:
									track2BPI = None
								try:
									track3BPI = int(task[3])
								except:
									track3BPI = None
								# Actual set
								self.setBPI(track1BPI, track2BPI, track3BPI)
							# Hi-Co mode set command
							elif taskCode == "h":
								self.setHiCo()
							# Lo-Co mode set command
							elif taskCode == "l":
								self.setLoCo()
							# Leading zeroes change command
							elif taskCode == "z":
								self.setLeadingZeroes(int(task[1]), int(task[2]))
							# Card erase command
							elif taskCode == "e":
								eraseTrack1 = False
								eraseTrack2 = False
								eraseTrack3 = False
								if (task[1] == "1") or ((len(task) > 2) and (task[2] == "1")) or ((len(task) > 3) and (task[3] == "1")):
									eraseTrack1 = True
								if (task[1] == "2") or ((len(task) > 2) and (task[2] == "2")) or ((len(task) > 3) and (task[3] == "2")):
									eraseTrack2 = True
								if (task[1] == "3") or ((len(task) > 2) and (task[2] == "3")) or ((len(task) > 3) and (task[3] == "3")):
									eraseTrack3 = True
								self.eraseCard(eraseTrack1, eraseTrack2, eraseTrack3)
							# Device model gathering command
							elif taskCode == "m":
								self.deviceModel()
							# Firmware version gathering command
							elif taskCode == "f":
								self.firmwareVersion()
							# All LEDs off command
							elif taskCode == "i0":
								self.allLEDOff()
							# Green LED on command
							elif taskCode == "i1":
								self.greenLED()
							# Green and yellow LEDs on command
							elif taskCode == "i2":
								self.greenAndYellowLED()
							# Red LED on command
							elif taskCode == "i3":
								self.redLED()
							# All LEDs on command
							elif taskCode == "i4":
								self.allLEDOn()
							# Silent mode on command
							elif taskCode == "p":
								self.dataOnlyMode = True
							# Communication test command
							elif taskCode == "tc":
								self.communicationTest()
							# Leading zeroes setting gathering command
							elif taskCode == "zs":
								self.getLeadingZeroes()
							# Coercivity setting gathering command
							elif taskCode == "gc":
								self.getCoercivity()
							# Sensor test command (PROBABLY UNSUPPORTED!)
							elif taskCode == "ts":
								self.sensorTest()
							# RAM test command (PROBABLY UNSUPPORTED!)
							elif taskCode == "tr":
								self.RAMTest()
							# Soft reset command
							elif taskCode == "sr":
								self.softReset()
							# Hard reset command
							elif taskCode == "hr":
								self.hardReset()
							# Unknown command
							else:
								if not self.dataOnlyMode:
									print("UNKNOWN COMMAND!")
					except:
						# Command failed
						if not self.dataOnlyMode:
							print("COMMAND FAILED!")
				# Close device at the end (if needed)
				self.close()
			# Arguments error
			else:
				self.headerDisplay()
				self.displayHelp()
		# Interpreter end
		return


# -------------------------------------------------------------------- #
#  Autorun section                                                     #
# -------------------------------------------------------------------- #

if __name__ == "__main__":
	cli = Interactive()
	cli.interpreter()
