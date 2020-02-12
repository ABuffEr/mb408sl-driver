# -*- coding: UTF-8 -*-
import addonHandler
import gui
import wx
import os
import sys
import config

addonHandler.initTranslation()

exePath = sys.path[-1]
configPath = config.getUserDefaultConfigPath()

# clean old manual setup
def onInstall():
	# try standard add-on removal
	for addon in addonHandler.getAvailableAddons():
		if addon.manifest['name'] in ("mb408", "MB408SLDriver"):
			if gui.messageBox(
				# Translators: the label of a message box dialog.
				_("Your old manual setup of MB408S/L driver will be deleted. Ensure to remember your manual changes before proceed."),
				# Translators: the title of a message box dialog.
				_("Cleaning old add-on"),
				wx.YES|wx.NO|wx.ICON_WARNING) == wx.YES:
				addon.requestRemove()
			break
	# force add-on removal
	forceRemove(configPath, "addons", "MB408")
	# remove .py
	forceRemove(configPath, "globalPlugins", "mb408sl.py")
	forceRemove(configPath, "scratchpad", "globalPlugins", "mb408sl.py")
	forceRemove(configPath, "brailleDisplayDrivers", "mb408sl.py")
	forceRemove(configPath, "scratchpad", "brailleDisplayDrivers", "mb408sl.py")
	forceRemove(exePath, "brailleDisplayDrivers", "mb408sl.py")
	# remove .dll
	forceRemove(configPath, "brailleDisplayDrivers", "mb408sl.dll")
	forceRemove(configPath, "scratchpad", "brailleDisplayDrivers", "mb408sl.dll")
	forceRemove(exePath, "brailleDisplayDrivers", "mb408sl.dll")

def forceRemove(*args):
	delPath = os.path.join(*args)
	if os.path.isdir(delPath):
		try:
			os.rmdir(delPath)
		except:
			pass
		return
	try:
		os.remove(delPath)
	except:
		pass
