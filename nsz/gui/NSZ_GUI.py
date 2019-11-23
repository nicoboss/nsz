from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from gui.ShaderWidget import *
from gui.RootWidget import *
from gui.GameList import *
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.settings import SettingsWithTabbedPanel
from kivy.logger import Logger
import os

class GUI(App):
	
	def run(self):
		super(GUI, self).run()
		return arguments(self.config)
	
	def build(self):
		Builder.load_file('gui/layout/GUI.kv')
		self.title = 'NSZ GUI'
		root = FloatLayout()
		with open("gui/shaders/plasma.shader") as stream:
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
		settings.add_json_panel('Settings', self.config, 'gui/json/settings_basic.json')
		settings.add_json_panel('Advanced', self.config, 'gui/json/settings_advanced.json')
		settings.add_json_panel('Tools', self.config, 'gui/json/settings_tools.json')

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


class arguments:
	def __init__(self, config):
		self.file = []
		self.C = None
		self.D = None
		self.output = None
		self.info = None
		self.extract = None
		self.create = None
		self.level = config.get('Settings', 'level')
		self.block = config.get('Settings', 'block')
		self.bs = config.get('Settings', 'bs')
		self.verify = config.get('Settings', 'verify')
		self.threads = config.get('Advanced', 'threads')
		self.parseCnmt = config.get('Advanced', 'parseCnmt')
		self.overwrite = config.get('Advanced', 'overwrite')
		self.rm_old_version = config.get('Advanced', 'rm_old_version')
		self.rm_source = config.get('Advanced', 'rm_source')
		self.depth = config.get('Tools', 'depth')


if __name__ == '__main__':
	GUI().run()
