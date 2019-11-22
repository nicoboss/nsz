from os import scandir
from pathlib import Path
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from FileDialogs import *

class RootWidget(FloatLayout):
	loadfile = ObjectProperty(None)
	savefile = ObjectProperty(None)
	text_input = ObjectProperty(None)
	gameList = None
	
	def __init__(self, gameList, **kwargs):
		Builder.load_file('layout/RootWidget.kv')
		super(RootWidget, self).__init__(**kwargs)
		self.ids.inFilesLayout.add_widget(gameList)
		self.gameList = gameList

	def dismissPopup(self):
		self._popup.dismiss()

	def showInputFileFolderDialog(self):
		content = OpenFileDialog(load=self.setInputFileFolder, cancel=self.dismissPopup)
		self._popup = Popup(title="Input File/Folder", content=content, size_hint=(0.9, 0.9))
		self._popup.open()

	def showOutputFileFolderDialog(self):
		content = OpenFileDialog(load=self.setOutputFileFolder, cancel=self.dismissPopup)
		self._popup = Popup(title="Output File/Folder", content=content, size_hint=(0.9, 0.9))
		self._popup.open()

	def setInputFileFolder(self, path, filename):
		fielist = []
		pathObj = Path(path)
		if pathObj.is_file():
			fielist.append(pathObj.name)
		elif  pathObj.is_dir():
			for file in scandir(path):
				fielist.append(Path(path).joinpath(file).name)
		self.gameList.refresh(fielist)
		self.dismissPopup()

	def setOutputFileFolder(self, path, filename):
		print(path)
		self.dismissPopup()
