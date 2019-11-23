from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from ShaderWidget import *
from RootWidget import *
from GameList import *
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.logger import Logger
import os

class GUI(App):
	def build(self):
		Builder.load_file('layout/GUI.kv')
		self.title = 'NSZ GUI'
		root = FloatLayout()
		with open("shaders/plasma.shader") as stream:
			plasma_shader = stream.read()
			root.add_widget(ShaderWidget(fs=plasma_shader))
		gameList = GameList()
		rootWidget = RootWidget(gameList)
		root.add_widget(rootWidget)
		self.settings_cls = MySettingsWithTabbedPanel
		#label = root.ids.label
		#label.text = self.config.get('My Label', 'text')
		#label.font_size = float(self.config.get('My Label', 'font_size'))
		#print(self.config.get('My Label', 'text'))
		return root

	def build_config(self, config):
		config.setdefaults(
		'Settings', {
			'level': 18,
			'block': False,
			'bs': 20,
			'verify': False,
		})
		config.setdefaults('Advanced', {
			'threads': -1,
			'parseCnmt': False,
			'overwrite': False,
			'rm_old_version': False,
			'rm_source': False,
		})
		config.setdefaults('Tools', {
			'depth': 1,
		})

	def build_settings(self, settings):
		settings.add_json_panel('Settings', self.config, 'json/settings_basic.json')
		settings.add_json_panel('Advanced', self.config, 'json/settings_advanced.json')
		settings.add_json_panel('Tools', self.config, 'json/settings_tools.json')

	def on_config_change(self, config, section, key, value):
		Logger.info("main.py: App.on_config_change: {0}, {1}, {2}, {3}".format(
			config, section, key, value))

		#if section == "My Label":
		#	if key == "text":
		#		self.root.ids.label.text = value
		#	elif key == 'font_size':
		#		self.root.ids.label.font_size = float(value)

	def close_settings(self, settings=None):
		Logger.info("main.py: App.close_settings: {0}".format(settings))
		super(GUI, self).close_settings(settings)
		
class MySettingsWithTabbedPanel(SettingsWithTabbedPanel):
	def on_close(self):
		Logger.info("main.py: MySettingsWithTabbedPanel.on_close")

	def on_config_change(self, config, section, key, value):
		Logger.info(
			"main.py: MySettingsWithTabbedPanel.on_config_change: "
			"{0}, {1}, {2}, {3}".format(config, section, key, value))


if __name__ == '__main__':
	GUI().run()
