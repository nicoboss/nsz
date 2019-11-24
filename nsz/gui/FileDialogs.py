from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
Builder.load_file('gui/layout/OpenFileDialog.kv')
Builder.load_file('gui/layout/SaveFileDialog.kv')

class OpenFileDialog(FloatLayout):
	load = ObjectProperty(None)
	cancel = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(OpenFileDialog, self).__init__(**kwargs)


class SaveFileDialog(FloatLayout):
	save = ObjectProperty(None)
	text_input = ObjectProperty(None)
	cancel = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(SaveFileDialog, self).__init__(**kwargs)
