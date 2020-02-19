# -*- coding: UTF-8 -*-
#brailleDisplayDrivers/mb248.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2011 Alberto Benassati <benassati@cavazza.it>
#
#changelog 15.01.2015:
#now, is possible to select COMport from setting dialog
#added some function associated to braille key

from logHandler import log
from ctypes import *
import inputCore
import wx
import braille
import os
from collections import OrderedDict
import serial
import hwPortUtils
import time

try:
	_basePath=os.path.dirname(__file__)
	mbDll=windll.LoadLibrary(_basePath+"\\mb248.dll")
except:
	mbDll=None

mbCellsMap=[]
KEY_CHECK_INTERVAL = 50

MB_KEYS = [
	"", "F1", "F2", "F3", "F4",  "F5", "F6", "F7", "F8", "F9", "F10", "LF", "UP", "RG", "DN", "",
	"", "SLF", "SUP", "SF3", "SDN",  "SF5", "SF6", "SF7", "SRG", "SF9", "SF10", "SLF", "SUP", "SRG", "SDN", "",
	"", "LF1", "LF2", "LF3", "LF4",  "LF5", "LF6", "LF7", "LF8", "LF9", "LF10", "LLF", "LUP", "LRG", "LDN", "",
	"", "SLF1", "SLF2", "SLF3", "SLF4",  "SLF5", "SLF6", "SLF7", "SLF8", "SLF9", "SLF10", "SLLF", "SLUP", "SLRG", "SLDN", "SFDN", "SFUP",
	"route"
]

def convertMbCells(cell):
	newCell = ((1<<6 if cell & 1<<4 else 0) |
		(1<<5 if cell & 1<<5  else 0) |
		(1<<0 if cell & 1<<6  else 0) |
		(1<<3 if cell & 1<<0  else 0) |
		(1<<2 if cell & 1<<1  else 0) |
		(1<<1 if cell & 1<<2  else 0) |
		(1<<7 if cell & 1<<3  else 0) |
		(1<<4 if cell & 1<<7  else 0))
	return newCell

class BrailleDisplayDriver(braille.BrailleDisplayDriver):
	name = "mb248"
	description = _("MDV MB248")

	@classmethod  
	def check(cls):
		return bool(mbDll)

	@classmethod
	def getPossiblePorts(cls):
		ports = OrderedDict()
		for p in hwPortUtils.listComPorts(): 
		# Translators: Name of a serial communications port 
			ports[p["port"]] = _("Serial: {portName}").format(portName=p["friendlyName"])
		return ports

	def  __init__(self,port):
		global mbCellsMap
		super(BrailleDisplayDriver, self).__init__()
		mbCellsMap=[convertMbCells(x) for x in range(256)]
		self._port = str(port) 
		log.info("MDV using port *"+self._port+"*")
		self._dev = None
		dic = -1
		log.info("try MDV using port "+self._port+" at baud 38400")
		if (mbDll.BrlInit(self._port, 38400)): 
			log.info("FOUND MDV using port "+self._port)
			self._keyCheckTimer = wx.PyTimer(self._handleKeyPresses)
			self._keyCheckTimer.Start(KEY_CHECK_INTERVAL)
			self._dev = 1
			dic = 1
		if (dic == -1):
			raise Exception("No or unknown braille display found "+self._port)
			
	def terminate(self):
		log.info("MDV close port "+self._port)
		super(BrailleDisplayDriver, self).terminate()
		try:
			mbDll.BrlTerminate()
			self._keyCheckTimer.Stop()
			self._keyCheckTimer = None
		except:
			pass
		time.sleep(2)
		

	def _get_numCells(self):
		return 24

	def _handleKeyPresses(self):
		while True:
			try:
				key=mbDll.ReadBuf()
			except:
				pass
			if not key: break
			if (key <= 64) or ((key >= 257) and (key <= 296)) or ((key >512) and (key < 769)):
				self._onKeyPress(key)

	def _onKeyPress(self, key):
		try:
			log.info("keys press".format(key))
			if (key >= 257) and (key <= 296):                                 
			    inputCore.manager.executeGesture(InputGesture(MB_KEYS[65],key-256))
			if (key <= 64):
			    inputCore.manager.executeGesture(InputGesture(MB_KEYS[key],0))
				
			if	(key>512) and (key<769): 
				key = key - 512
				keydot = 0
				keydots = set()
				
				if (key & 1):
					keydots.add("b1")
				if (key & 2):
					keydots.add("b2")
				if (key & 4):
					keydots.add("b3")
				if (key & 8):
					keydots.add("b4")
				if (key & 16):
					keydots.add("b5")
				if (key & 32):
					keydots.add("b6")
				if (key & 64):
					keydots.add("b7")
				if (key & 128):
					keydots.add("b8")
				data = "+".join(keydots)
				try:
					log.info("keys {keys}".format(keys=data))
					inputCore.manager.executeGesture(InputGesture(data,0))
				except inputCore.NoInputGestureAction:
					log.debug("No Action for keys {keys}".format(keys=data))
					pass				
				
		except inputCore.NoInputGestureAction:
			pass

	def display(self, cells):
		cells="".join(chr(mbCellsMap[x]) for x in cells)
		mbDll.WriteBuf(cells) 

	gestureMap = inputCore.GlobalGestureMap({
		"globalCommands.GlobalCommands": {
			"braille_routeTo": ("br(mb248):route",),
			"braille_scrollBack": ("br(mb248):LF",),
			"braille_previousLine": ("br(mb248):UP",),
			"braille_nextLine": ("br(mb248):DN",),
			"braille_scrollForward": ("br(mb248):RG",),	
			
#           "kb:shift+tab": ("br(mb408sl):SLF",),
#			"kb:tab": ("br(mb408sl):SRG",),
#			"kb:alt+tab": ("br(mb408sl):SDN",),
#			"kb:alt+shift+tab": ("br(mb408sl):SUP",),

            "kb:leftArrow": ("br(mb248):SLF",),
			"kb:rightArrow": ("br(mb248):SRG",),
			"kb:downArrow": ("br(mb248):SDN",),
			"kb:upArrow": ("br(mb248):SUP",),
			
			"braille_toggleTether": ("br(mb248):b1+b4",), 
			"navigatorObject_previous": ("br(mb248):b2",), 
			"navigatorObject_next": ("br(mb248):b5",), 
			"navigatorObject_parent": ("br(mb248):b3",), 
			"navigatorObject_firstChild": ("br(mb248):b6",), 
			"title": ("br(mb248):b1",), 


			"kb:enter": ("br(mb248):b4+b5",), 
			"kb:tab": ("br(mb248):b2+b3+b4+b5",),
			"kb:shift+tab": ("br(mb248):b1+b2+b5+b6",),
			"kb:control+home": ("br(mb248):b1+b2+b3",),
			"kb:control+end": ("br(mb248):b4+b5+b6",),
			"kb:alt": ("br(mb248):b1+b3+b4",),
			"kb:escape": ("br(mb248):b1+b2",), 			
			"kb:home": ("br(mb248):b2+b3",),	
			"kb:end": ("br(mb248):b5+b6",),
			"kb:backspace": ("br(mb248):b8",), 			
			"kb:Pageup": ("br(mb248):b1+b2+b3+b4",),
			"kb:Pagedown": ("br(mb248):b1+b4+b5+b6",),
			"kb:control+t": ("br(mb248):b1+b2+b4",),
			"kb:alt+tab": ("br(mb248):b2+b4",),
			"kb:windows+d": ("br(mb248):b1+b4+b5",),


			"kb:alt+F4": ("br(mb248):b1+b4+b7",), 			
			




			"reportStatusLine": ("br(mb248):b4",) 
        }
	})

	

class InputGesture(braille.BrailleDisplayGesture):

	source = BrailleDisplayDriver.name

	def __init__(self, command, argument):
		super(InputGesture, self).__init__()
		self.id = command
		if (command == MB_KEYS[65]):
			self.routingIndex = argument
                
