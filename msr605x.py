#!/usr/bin/env python3

# Simple MSR605X driver
#
# by Magnetic-Fox, 02-03.04.2026
#
# (C)2026 Bartłomiej "Magnetic-Fox" Węgrzyn


import hid

# Main device class
class MSR605X:
	# Default values (VID + PID for MSR605X and additionals)
	DEFAULT_VID = 0x0801
	DEFAULT_PID = 0x0003
	DEFAULT_RID = b"\xff"
	DEFAULT_TIMEOUT = 100
	DEFAULT_FIRST_TIMEOUT = 1000
	
	# Command and typical constants
	ESC = b"\x1b"
	
	NO_DATA = ESC + b"+"
	START_SEQUENCE = ESC + b"s"
	END_SEQUENCE = b"?\x1c" + ESC
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
#	CMD_SENSOR_TEST = ESC + b"\x86"
#	CMD_RAM_TEST = ESC + b"\x87"

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
	
	TRACK1 = 1
	TRACK2 = 2
	TRACK3 = 4
	
	CMD_OK = b"\x1b0"
	CMD_FAIL = b"\x1bA"
	
	RW_ERROR = b"\x1b1"
	CMD_ERROR = b"\x1b2"
	CMD_INVALID = b"\x1b4"
	SWIPE_ERROR = b"\x1b9"
	COMM_OK = b"\x1by"
	SETTING_ACK = b"\x1b0"
	HICO_SET = b"\x1bh"
	LOCO_SET = b"\x1bl"
	
	# Class init and device connection initialization constructor method
	def __init__(self, vendorID = DEFAULT_VID, productID = DEFAULT_PID, reportID = DEFAULT_RID, timeout = DEFAULT_TIMEOUT, firstTimeout = DEFAULT_FIRST_TIMEOUT):
		self.vendorID = vendorID
		self.productID = productID
		self.reportID = reportID
		self.timeout = timeout
		self.firstTimeout = firstTimeout
		
		self.rawData = b""
		
		self.hidDevice = hid.device()
		self.hidDevice.open(self.vendorID, self.productID)
		return
		
	# Device freeing method
	def close(self):
		self.hidDevice.close()
		return
		
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
		
	# Read automation method (read + concat with timeout)
	def readData(self, firstTimeout = None):
		self.rawData = b""
		
		if firstTimeout != None:
			timeout = firstTimeout
		else:
			timeout = self.timeout
		
		while True:
			if(temp := self.hidDevice.read(64, timeout)[1:]):
				self.rawData += bytes(temp)
				if timeout != self.timeout:
					timeout = self.timeout
			else:
				if firstTimeout == None:
					break
				else:
					if len(self.rawData) > 0:
						break
			
		return

	# Read data export method (ISO 7811 - tracks 1, 2, 3)
	def exportISOData(self):
		status = b"\x00"
		iso1 = None
		iso2 = None
		iso3 = None
		
		try:
			if self.rawData[0:2] == self.START_SEQUENCE:
				iso1pos = self.rawData.find(self.ISO1_DATA_START) + 2
				iso2pos = self.rawData.find(self.ISO2_DATA_START) + 2
				iso3pos = self.rawData.find(self.ISO3_DATA_START) + 2
				endStatusPos = self.rawData.find(self.END_SEQUENCE) + 3
				
				iso1 = self.rawData[iso1pos:iso2pos - 2]
				iso2 = self.rawData[iso2pos:iso3pos - 2]
				iso3 = self.rawData[iso3pos:endStatusPos - 3]
				
				status = self.rawData[endStatusPos:endStatusPos + 1]
				
				if (iso1[0] == ord("%")) and (iso1[-1] == ord("?")):
					iso1 = iso1[1:][:-1]
					
				elif iso1 == self.NO_DATA:
					iso1 = b""
					
				if (iso2[0] == ord(";")) and (iso2[-1] == ord("?")):
					iso2 = iso2[1:][:-1]
					
				elif iso2 == self.NO_DATA:
					iso2 = b""
					
				if (iso3[0] == ord(";")) and (iso3[-1] == ord("?")):
					iso3 = iso3[1:][:-1]
					
				elif iso3 == self.NO_DATA:
					iso3 = b""
			
		except:
			pass
		
		return status, iso1, iso2, iso3
		
	# Reset command send method
	def reset(self):
		self.writeData(self.CMD_RESET)
		return
		
	# Read command method (fully automated)
	def read(self, sendCommand = True):
		if sendCommand:
			self.writeData(self.CMD_READ)
			
		self.readData(self.firstTimeout)
		
		return self.exportISOData()
		
	
	
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
			if self.rawData[0].to_bytes() == b"\x1b":
				return self.rawData[1], self.rawData[2]
			else:
				return 0, 0
		else:
			return 0, 0
	
	# Device model get method
	def getDeviceModel(self):
		self.writeData(self.CMD_GET_MODEL)
		self.readData()
		if len(self.rawData) >= 3:
			if (self.rawData[0].to_bytes() == b"\x1b") and (self.rawData[2].to_bytes() == b"S"):
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
			if self.rawData[0].to_bytes() == b"\x1b":
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
			return self.rawData[0:2] == self.SETTING_ACK
		else:
			return False

	# Lo-Co set method
	def setLoCo(self):
		self.writeData(self.CMD_SET_LOCO)
		self.readData()
		if len(self.rawData) >= 2:
			return self.rawData[0:2] == self.SETTING_ACK
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
