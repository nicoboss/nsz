from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.utils import platform
from nsz.gui.GuiPath import *

Builder.load_file(getGuiPath('layout/OpenFileDialog.kv'))
Builder.load_file(getGuiPath('layout/SaveFileDialog.kv'))


class OpenFileDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(OpenFileDialog, self).__init__(**kwargs)
		for drive in WinDrives.get_win_drives():
			self.ids.drives_list.add_widget(Button(text=drive, on_press=self.drive_selection_changed))
	
	def drive_selection_changed(self, *args):
		self.ids.filechooser.path = args[0].text

class SaveFileDialog(FloatLayout):
	save = ObjectProperty(None)
	text_input = ObjectProperty(None)
	cancel = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(SaveFileDialog, self).__init__(**kwargs)
		for drive in WinDrives.get_win_drives():
			self.ids.drives_list.add_widget(Button(text=drive, on_press=self.drive_selection_changed))
	
	def drive_selection_changed(self, *args):
		self.ids.filechooser.path = args[0].text


class WinDrives:
	def get_win_drives():
		if platform == 'win':
			import win32api

			drives = win32api.GetLogicalDriveStrings()
			drives = drives.split('\000')[:-1]

			return drives
		else:
			return []

