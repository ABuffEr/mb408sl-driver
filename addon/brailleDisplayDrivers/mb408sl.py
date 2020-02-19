# -*- coding: UTF-8 -*-
# mb408s/l driver
# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2011 Alberto Benassati <benassati@cavazza.it>
# for main initial development;
# Copyright (C) 2020 Alberto Buffolino <a.buffolino@gmail.com>
# for NVDA 2019.3 add-on packaging and fixes;
# and various others (not easily discoverable)
# for port selection and gesture additions

from logHandler import log
from ctypes import *
import inputCore
import wx
import braille
import os
from collections import OrderedDict
import hwPortUtils
import addonHandler
import sys
import config
from speech import speakMessage, Spri

py3 = sys.version.startswith("3")

mbCellsMap = []
KEY_CHECK_INTERVAL = 50
MB_KEYS = [
	"", "F1", "F2", "F3", "F4",  "F5", "F6", "F7", "F8", "F9", "F10", "LF", "UP", "RG", "DN", "",
	"", "SF1", "SF2", "SF3", "SF4",  "SF5", "SF6", "SF7", "SF8", "SF9", "SF10", "SLF", "SUP", "SRG", "SDN", "",
	"", "LF1", "LF2", "LF3", "LF4",  "LF5", "LF6", "LF7", "LF8", "LF9", "LF10", "LLF", "LUP", "LRG", "LDN", "",
	"", "SLF1", "SLF2", "SLF3", "SLF4",  "SLF5", "SLF6", "SLF7", "SLF8", "SLF9", "SLF10", "SLLF", "SLUP", "SLRG", "SLDN", "SFDN", "SFUP",
	"route"
]
mbDll = None
mbBaud = None

def loadDll():
	global mbDll
	if mbDll:
		try:
			windll.kernel32.FreeLibrary(mbDll._handle)
		except:
			pass
	dllFilePath = os.path.join(os.path.dirname(__file__), "mb408sl.dll")
	if isinstance(dllFilePath, bytes):
		dllFilePath = dllFilePath.decode("mbcs")
	try:
		mbDll = windll.LoadLibrary(dllFilePath)
	except:
		pass

def loadBaud():
	global mbBaud
	try:
		mbBaud = int(config.conf["braille"]["mb408sl"]["baud"])
	except:
		pass

def resetBaud():
	global mbBaud
	config.conf["braille"]["mb408sl"]["baud"] = mbBaud = None

def saveBaud():
	config.conf["braille"]["mb408sl"]["baud"] = mbBaud

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

loadDll()
loadBaud()

class BrailleDisplayDriver(braille.BrailleDisplayDriver):

	name = "mb408sl"
	description = "MDV MB408S/L"

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

	def __init__(self, port):
		global mbCellsMap, mbBaud, mbDll
		super(BrailleDisplayDriver, self).__init__()
		mbCellsMap = [convertMbCells(x) for x in range(256)]
		if mbBaud:
			log.info("Try MDV on port %s at saved baud %d"%(port, mbBaud))
		else:
			log.info("Try MDV on port %s at baud 38400 and 19200"%port)
		mbPort = bytes(port.encode("mbcs"))
		mbFound = False
		bauds = (mbBaud,) if mbBaud else (38400, 19200)
		if not mbBaud:
			speakMessage(_("Please wait"), Spri.NOW)
		for baud in bauds:
			log.info("Trying baud %d"%baud)
			if mbDll.BrlInit(mbPort, baud):
				mbBaud = baud
				mbFound = True
				log.info("Found MDV on port %s at baud %d"%(port, baud))
				break
		if not mbFound:
			resetBaud()
			loadDll()
			raise RuntimeError("No MB408 display found")
		else:
			self._keyCheckTimer = wx.PyTimer(self._handleKeyPresses)
			self._keyCheckTimer.Start(KEY_CHECK_INTERVAL)
			saveBaud()

	def terminate(self):
		log.info("MDV terminate")
		super(BrailleDisplayDriver, self).terminate()
		try:
			mbDll.BrlTerminate()
			self._keyCheckTimer.Stop()
			self._keyCheckTimer = None
		except:
			pass

	def _get_numCells(self):
		return 40

	def _handleKeyPresses(self):
		while True:
			try:
				key = mbDll.ReadBuf()
			except:
				pass
			if not key: break
			if (key <= 64) or ((key >= 257) and (key <= 296)):
				self._onKeyPress(key)

	def _onKeyPress(self, key):
		try:
			if (key >= 257) and (key <= 296):
				inputCore.manager.executeGesture(InputGesture(MB_KEYS[65],key-256))
			if (key <= 64):
				inputCore.manager.executeGesture(InputGesture(MB_KEYS[key],0))
		except inputCore.NoInputGestureAction:
			pass

	def display(self, cells):
		cells="".join(chr(mbCellsMap[x]) for x in cells)
		if py3:
			cells = bytes(cells.encode("raw_unicode_escape"))
		mbDll.WriteBuf(cells)

	gestureMap = inputCore.GlobalGestureMap({
		"globalCommands.GlobalCommands": {
			"braille_routeTo": ("br(mb408sl):route",),
			"braille_scrollBack": ("br(mb408sl):LF",),
			"braille_previousLine": ("br(mb408sl):UP",),
			"braille_nextLine": ("br(mb408sl):DN",),
			"braille_scrollForward": ("br(mb408sl):RG",),	

#			"kb:shift+tab": ("br(mb408sl):SLF",),
#			"kb:tab": ("br(mb408sl):SRG",),
#			"kb:alt+tab": ("br(mb408sl):SDN",),
#			"kb:alt+shift+tab": ("br(mb408sl):SUP",),

			"kb:leftArrow": ("br(mb408sl):SLF",),
			"kb:rightArrow": ("br(mb408sl):SRG",),
			"kb:downArrow": ("br(mb408sl):SDN",),
			"kb:upArrow": ("br(mb408sl):SUP",),

			"braille_toggleTether": ("br(mb408sl):F5",),
			"review_currentCharacter": ("br(mb408sl):F4",),
			"review_activate": ("br(mb408sl):F3",),
			"reportFormatting": ("br(mb408sl):F10",),

			"navigatorObject_previous": ("br(mb408sl):F6",),
			"navigatorObject_next": ("br(mb408sl):F7",),
			"navigatorObject_parent": ("br(mb408sl):F8",),
			"navigatorObject_firstChild": ("br(mb408sl):F9",),

			"title": ("br(mb408sl):F1",),
			"reportStatusLine": ("br(mb408sl):F2",),
		}
	})

class InputGesture(braille.BrailleDisplayGesture):

	source = BrailleDisplayDriver.name

	def __init__(self, command, argument):
		super(InputGesture, self).__init__()
		self.id = command
		if (command == MB_KEYS[65]):
			self.routingIndex = argument
