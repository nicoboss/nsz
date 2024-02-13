from os import scandir
from pathlib import Path
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from functools import partial
from nsz.gui.DraggableScrollbar import *
from nsz.gui.GuiPath import *
from nsz.PathTools import *
from nsz import FileExistingChecks
from traceback import print_exc

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
	
	touchedIndex = -1
	
	def __init__(self, **kwargs):
		super(SelectableRecycleBoxLayout, self).__init__(**kwargs)
		self.unfocus_on_touch = False
	
	def keyboard_on_key_down(self, window, keycode, text, modifiers):
		keycodeId, keycodeName = keycode
		if keycodeName == 'delete' or keycodeName == 'backspace' and len(self.selected_nodes) > 0:
			for index in self.selected_nodes:
				del self.parent.parent.parent.filelist[self.parent.data[index]['0']]
			self.clear_selection()
			self.parent.parent.parent.refresh()
			return True
		if 'ctrl' in modifiers:
			if keycodeName == 'a':
				for index in range(len(self.parent.data)):
					self.select_node(index)
		return False


class SelectableLabel(RecycleDataViewBehavior, GridLayout):
	index = None
	selected = BooleanProperty(False)
	selectable = BooleanProperty(True)
	cols = 4

	def refresh_view_attrs(self, rv, index, data):
		self.index = index
		self.filename_text = data['0']
		self.titleid = data['1']
		self.version = data['2']
		self.filesize_text = data['3']
		return super(SelectableLabel, self).refresh_view_attrs(
			rv, index, data)

	def on_touch_down(self, touch):
		if super(SelectableLabel, self).on_touch_down(touch):
			return True
		if self.collide_point(*touch.pos) and self.selectable:
			self.parent.touchedIndex = self.index
			return self.parent.select_with_touch(self.index, touch)
	
	def on_touch_move(self, touch):
		if super(SelectableLabel, self).on_touch_move(touch):
			return True
		if self.parent.touchedIndex != self.index and self.collide_point(*touch.pos) and self.selectable:
			self.parent.touchedIndex = self.index
			return self.parent.select_with_touch(self.index, touch)

	def apply_selection(self, rv, index, is_selected):
		self.selected = is_selected


class RV(RecycleView):
	def __init__(self, items, **kwargs):
		super(RV, self).__init__(**kwargs)
		self.refresh(items)
		
	def refresh(self, items):
		self.data.clear()
		for path in items:
			self.data.append({'0': path, '1': items[path][0], '2': 'v' + str(items[path][1]), '3': self.sizeof_fmt(items[path][2])})
		self.refresh_from_data()
			
	def sizeof_fmt(self, num, suffix='B'):
		for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
			if abs(num) < 1024.0:
				return "%3.1f %s%s" % (num, unit, suffix)
			num /= 1024.0
		return "%.1f%s%s" % (num, 'Yi', suffix)


class GameList(StackLayout):

	filelist = {}
	recycleView = None
	draggableScrollbar = None

	def __init__(self, **kwargs):
		Builder.load_file(getGuiPath('layout/GameList.kv'))
		super(GameList, self).__init__(**kwargs)
		self.recycleView = RV([])
		self.draggableScrollbar = DraggableScrollbar(self.recycleView)
		self.add_widget(self.draggableScrollbar)
		self.draggableScrollbar.slider.opacity = 0
		Window.bind(on_dropfile=self.handledrops)
		self.name = "gameList"

	def handledrops(self, widget, rawPath):
		path = Path(rawPath.decode('utf-8')).absolute()
		self.addFiles(path)
		
	def addFiles(self, path):
		fullPath = str(path.resolve())
		try:
			if path.is_dir():
				requireRefresh = False
				for file in scandir(str(path)):
					filepath = path.joinpath(file)
					if isGame(filepath) or isCompressedGameFile(filepath):
						filepathStr = str(filepath.resolve())
						if isGame(filepath):
							extractedIdVersion = FileExistingChecks.ExtractTitleIDAndVersion(filepathStr)
							if extractedIdVersion is None:
								print(f'Failed to extract TitleID/Version from filename "{Path(filepathStr).name}"')
								extractedIdVersion = ("None", 0)
							(titleIDExtracted, versionExtracted) = extractedIdVersion
						else:
							(titleIDExtracted, versionExtracted) = ("None", 0)
						if not filepathStr in self.filelist:
							requireRefresh = True
							self.filelist[filepathStr] = (titleIDExtracted, versionExtracted, filepath.stat().st_size)
				if requireRefresh:
					self.refresh()
			elif path.is_file():
				if isGame(path) or isCompressedGameFile(path):
					if isGame(path):
						extractedIdVersion = FileExistingChecks.ExtractTitleIDAndVersion(fullPath)
						if extractedIdVersion is None:
							print(f'Failed to extract TitleID/Version from filename "{Path(fullPath).name}"')
							extractedIdVersion = ("None", 0)
						(titleIDExtracted, versionExtracted) = extractedIdVersion
					else:
						(titleIDExtracted, versionExtracted) = ("None", 0)
					if not fullPath in self.filelist:
						self.filelist[fullPath] = (titleIDExtracted, versionExtracted, path.stat().st_size)
						self.refresh()
			else:
				print("Warning: {0} isn't a file or folder!".format(fullPath))
		except BaseException as e:
			print('Error while adding {0} to gamelist: {1}'.format(fullPath, str(e)))
			print_exc()

	def refresh(self):
		if self.ids.DragAndDropFloatLayout:
			self.remove_widget(self.ids.DragAndDropFloatLayout)
		self.draggableScrollbar.slider.opacity = int(len(self.filelist) > 20)
		self.recycleView.refresh(self.filelist)

	def scroll_change(self, recycleView, instance, value):
		recycleView.scroll_y = value

	def slider_change(self, s, instance, value):
		if value >= 0:
		#this to avoid 'maximum recursion depth exceeded' error
			s.value=value
