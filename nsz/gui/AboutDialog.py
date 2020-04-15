from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.popup import Popup
from nsz.gui.Hyperlink import *
from kivy.core.window import Window
from nsz.gui.GuiPath import *
import os

Builder.load_file(getGuiPath('layout/AboutDialog.kv'))


class AboutDialog(FloatLayout):
	cancel = ObjectProperty(None)
	
	def __init__(self, **kwargs):
		super(AboutDialog, self).__init__(**kwargs)
		with open(getGuiPath("txt/license.txt")) as stream:
			self.ids.license_text.text = stream.read()
			
	def remove_widget_recursive(self, children):
		for child in children:
			if len(child.children) > 0:
				self.remove_widget_recursive(child.children)
			if isinstance(child, HyperlinkLabel):
				child.unbind()
			child.remove_widget(child)
			
	def closeAboutDialog(self, **kwargs):
		self.remove_widget_recursive(self.children)
		self.cancel()
