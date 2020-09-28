from os import scandir
from pathlib import Path
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from nsz.gui.FileDialogs import *
from nsz.gui.AboutDialog import *
from nsz.gui.GuiPath import *
from nsz.PathTools import *
from nsz import FileExistingChecks

class RootWidget(FloatLayout):
	loadfile = ObjectProperty(None)
	savefile = ObjectProperty(None)
	text_input = ObjectProperty(None)
	gameList = None
	
	hardExit = True
	C = False
	D = False
	output = False
	verify = False
	info = False
	titlekeys = False
	extract = False
	create = False
	
	def __init__(self, gameList, **kwargs):
		Builder.load_file(getGuiPath('layout/RootWidget.kv'))
		super(RootWidget, self).__init__(**kwargs)
		self.ids.inFilesLayout.add_widget(gameList)
		self.gameList = gameList
		
	def Compress(self):
		self.C = True
		self.hardExit = False
		App.get_running_app().stop()
		
	def Decompress(self):
		self.D = True
		self.hardExit = False
		App.get_running_app().stop()
		
	def Verify(self):
		self.verify = True
		self.hardExit = False
		App.get_running_app().stop()
		
	def Info(self):
		self.info = True
		self.hardExit = False
		App.get_running_app().stop()
		
	def Titlekeys(self):
		self.titlekeys = True
		self.hardExit = False
		App.get_running_app().stop()
		
	def Extract(self):
		self.extract = True
		self.hardExit = False
		App.get_running_app().stop()

	def dismissPopup(self):
		self._popup.dismiss()

	def showInputFileFolderDialog(self):
		filter = ['*.nsp', '*.nsz', '*.xci', '*.xcz', '*.ncz']
		content = OpenFileDialog(load=self.setInputFileFolder, cancel=self.dismissPopup, filters=filter)
		self._popup = Popup(title="Input File/Folder", content=content, size_hint=(0.9, 0.9))
		self._popup.open()

	def showOutputFileFolderDialog(self):
		content = OpenFileDialog(load=self.setOutputFileFolder, cancel=self.dismissPopup, filters=[self.showNoFiles])
		self._popup = Popup(title="Output File/Folder", content=content, size_hint=(0.9, 0.9))
		self._popup.open()
		
	def showNoFiles(self, foldername, filename):
		return False

	def setInputFileFolder(self, rawPath, filename):
		if len(filename) == 0:
			return
		path = Path(rawPath).joinpath(filename[0])
		if len(filename) == 1:
			self.gameList.addFiles(path)
		else:
			for file in filename[1:]:
				filepath = path.joinpath(file)
				self.gameList.addFiles(filepath)
		self.dismissPopup()

	def setOutputFileFolder(self, path, filename):
		self.output = path
		print("Set --output to {0}".format(self.output))
		self.dismissPopup()
		
	def showAboutDialog(self):
		content = AboutDialog(cancel=self.dismissPopup)
		self._popup = Popup(title="About", content=content, auto_dismiss=False, size_hint=(0.9, 0.9))
		self._popup.open()
