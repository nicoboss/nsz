from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.utils import platform
from nsz.gui.GuiPath import *

Builder.load_file(getGuiPath('layout/OpenFileDialog.kv'))


class OpenFileDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)
	filters = ObjectProperty(None)
	selected = None
	backgroundColor = [1, 1, 1, 1]
	selectedColor = [1.4, 1.4, 1.4, 1]
	buttonDown = 'atlas://data/images/defaulttheme/button'
	
	def __init__(self, **kwargs):
		super(OpenFileDialog, self).__init__(**kwargs)
		self.ids.filechooser.filters = self.filters
		drives = WinDrives.get_win_drives()
		if len(drives) == 0:
			self.ids.drives_list.height = 0
		else:
			for drive in drives:
				button = Button(text=drive, background_color=self.backgroundColor, background_down=self.buttonDown, on_press=self.drive_selection_changed)
				self.ids.drives_list.add_widget(button)
				if self.selected == None:
					self.drive_selection_changed(button)
	
	def drive_selection_changed(self, *args):
		self.ids.filechooser.path = args[0].text
		if self.selected != None:
			self.selected.background_color = self.backgroundColor
		self.selected = args[0]
		args[0].background_color = self.selectedColor


class WinDrives:
	def get_win_drives():
		if platform == 'win':
			import win32api

			drives = win32api.GetLogicalDriveStrings()
			drives = drives.split('\000')[:-1]

			return drives
		else:
			return []

