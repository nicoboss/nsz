from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.compat import string_types
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.factory import Factory
from kivy.lang import Builder
from nsz.gui.GuiPath import *
import webbrowser

Builder.load_file(getGuiPath('layout/Hyperlink.kv'))


class Tooltip(Label):
	pass

class HyperlinkTooltip(BoxLayout):
	pass

class HyperlinkLabel(ButtonBehavior, Label):
	tooltip = StringProperty('')
	url = StringProperty('')
	url_text = StringProperty('')
	tooltip_show = False
	url_mouseover = False
	

	def __init__(self, **kwargs):
		self._tooltip = None
		super(HyperlinkLabel, self).__init__(**kwargs)
		Window.bind(mouse_pos=self.on_mouse_pos)
		self.fbind('tooltip', self._update_tooltip)
		self.fbind('url', self._update_text)
		self.fbind('url_text', self._update_text)
		
	def unbind(self):
		Window.unbind(mouse_pos=self.on_mouse_pos)
		self.funbind('tooltip', self._update_tooltip)
		self.funbind('url', self._update_text)
		self.funbind('url_text', self._update_text)
	
	def _update_tooltip(self, *args):
		if self.tooltip == '':
			self.tooltip = None
		else:
			self._tooltip = Tooltip()
	
	def _update_text(self, *args):
		if self.tooltip == '':
			self.tooltip = self.url
		if not self.url_mouseover:
			self.text = "[u][color=#00FFFF][ref={0}][/ref]{1}[/color][/u]".format(self.url, self.url_text)
		else:
			self.text = "[u][color=#FFFF00][ref={0}][/ref]{1}[/color][/u]".format(self.url, self.url_text)

	def on_mouse_pos(self, *args):
		if not self._tooltip == None:
			self._tooltip.pos = args[1]
		if self.collide_point(*self.to_widget(*args[1])):
			if not self.url_mouseover:
				self.url_mouseover = True
				Window.set_system_cursor("hand")
				self._update_text(*args)
				if not self._tooltip == None:
					Clock.schedule_once(self.display_tooltip, 0.5)
		elif self.url_mouseover:
			self.url_mouseover = False
			Window.set_system_cursor("arrow")
			self._update_text(*args)
			if not self._tooltip == None:
				Clock.unschedule(self.display_tooltip)
				self.close_tooltip()

	def on_press(self):
		webbrowser.open(self.url)

	def close_tooltip(self, *args):
		Window.remove_widget(self._tooltip)

	def display_tooltip(self, *args):
		self.tooltip_show = True
		self._tooltip.text = self.tooltip
		Window.add_widget(self._tooltip)
