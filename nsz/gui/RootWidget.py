from os import scandir
from pathlib import Path
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from gui.FileDialogs import *
from gui.AboutDialog import *
from nsz.gui.GuiPath import *
from PathTools import *

class RootWidget(FloatLayout):
	loadfile = ObjectProperty(None)
	savefile = ObjectProperty(None)
	text_input = ObjectProperty(None)
	gameList = None
	
	hardExit = True
	C = False
	D = False
	output = False
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
		
		self.C = True
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

	def setInputFileFolder(self, path, filename):
		if len(filename) == 0:
			pathObj = Path(path)
			if pathObj.is_dir():
				for file in scandir(path):
					filepath = Path(path).joinpath(file)
					if isGame(filepath) or isCompressedGameFile(filepath):
						self.gameList.filelist[str(filepath.resolve())] = filepath.stat().st_size
		else:
			for file in filename:
				filepath = Path(path).joinpath(file)
				if filepath.is_file():
					self.gameList.filelist[str(filepath.resolve())] = filepath.stat().st_size
		self.gameList.refresh()
		self.dismissPopup()

	def setOutputFileFolder(self, path, filename):
		self.output = path
		print("Set --output to {0}".format(self.output))
		self.dismissPopup()
		
	def showAboutDialog(self):
		content = AboutDialog(cancel=self.dismissPopup)
		self._popup = Popup(title="About", content=content, auto_dismiss=False, size_hint=(0.9, 0.9))
		self._popup.open()
