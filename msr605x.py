#!/usr/bin/env python3

# Simple MSR605X driver
#
# by Magnetic-Fox, 02-04.04.2026
#
# (C)2026 Bartłomiej "Magnetic-Fox" Węgrzyn


import hid

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
		self.open()
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
		
	# Timeout method set method
	def setTimout(self, timeout):
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
					iso1 = iso1[1:][:-1]

				# Return empty byte-string on no data
				elif iso1 == self.NO_DATA:
					iso1 = b""
					
				# Return nothing on bad data
				elif iso1 == self.BAD_DATA:
					iso1 = None
				
				# ISO 7811 - Track 2
				# Strip start and end sentinels (if they are there)	
				if (iso2[0] == ord(self.START_SENTINEL_2_3)) and (iso2[-1] == ord(self.END_SENTINEL)):
					iso2 = iso2[1:][:-1]
				
				# Return empty byte-string on no data	
				elif iso2 == self.NO_DATA:
					iso2 = b""
				
				# Return nothing on bad data
				elif iso2 == self.BAD_DATA:
					iso2 = None

				# ISO 7811 - Track 3
				# Strip start and end sentinels (if they are there)
				if (iso3[0] == ord(self.START_SENTINEL_2_3)) and (iso3[-1] == ord(self.END_SENTINEL)):
					iso3 = iso3[1:][:-1]
					
				# Return empty byte-string on no data
				elif iso3 == self.NO_DATA:
					iso3 = b""
				
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
