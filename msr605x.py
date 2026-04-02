#!/usr/bin/env python3

# Simple MSR605X driver
#
# by Magnetic-Fox, 02.04.2026
#
# (C)2026 Bartłomiej "Magnetic-Fox" Węgrzyn


import hid


class MSR605X:
	DEFAULT_VID = 0x0801
	DEFAULT_PID = 0x0003
	DEFAULT_RID = b"\xff"
	DEFAULT_TIMEOUT = 100
	DEFAULT_FIRST_TIMEOUT = 10000
	
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
	CMD_SENSOR_TEST = ESC + b"\x86"
	CMD_RAM_TEST = ESC + b"\x87"
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
	
	RW_OK = b"0"
	RW_ERROR = b"1"
	CMD_ERROR = b"2"
	CMD_INVALID = b"4"
	SWIPE_ERROR = b"9"
	
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
		
	def close(self):
		self.hidDevice.close()
		return
		
	def dataSplit(self, data, size):
		return [data[i:i + size] for i in range(0, len(data), size)]
		
	def dataFill(self, data, size):
		return data + b"\x00" * (size - len(data))
		
	def writeData(self, data):
		dataChunks = self.dataSplit(data, 64)
		for dataChunk in dataChunks:
			self.hidDevice.write(self.reportID + self.dataFill(dataChunk, 64))
		return
		
	def readData(self, firstTimeout = None):
		self.rawData = b""
		
		if firstTimeout != None:
			timeout = firstTimeout
		else:
			timeout = self.timeout
		
		while(temp := self.hidDevice.read(256, timeout)[1:]):
			self.rawData += bytes(temp)
			if timeout != self.timeout:
				timeout = self.timeout
			
		return

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
		
	def reset(self):
		self.writeData(self.CMD_RESET)
		return
		
	def read(self, sendCommand = True):
		if sendCommand:
			self.writeData(self.CMD_READ)
			
		self.readData(self.firstTimeout)
		
		return self.exportISOData()
		
	def allLedOff(self):
		self.writeData(self.CMD_ALL_LED_OFF)
		return
		
	def allLedOn(self):
		self.writeData(self.CMD_ALL_LED_ON)
		return
		
	def greenLedOn(self):
		self.writeData(self.CMD_GREEN_LED_ON)
		return
		
	def yellowLedOn(self):
		self.writeData(self.CMD_YELLOW_LED_ON)
		return

	def redLedOn(self):
		self.writeData(self.CMD_RED_LED_ON)
		return
