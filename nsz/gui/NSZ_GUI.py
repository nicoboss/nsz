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
from nsz.gui.GuiPath import *
from nsz.gui.SettingScrollOptions import *
import os

class GUI(App):
	
	rootWidget = None
	
	def run(self):
		super(GUI, self).run()
		if not self.rootWidget.hardExit:
			return arguments(self.config, self.rootWidget)
		else:
			return None
	
	def build(self):
		Builder.load_file(getGuiPath('layout/GUI.kv'))
		self.title = 'NSZ GUI 3.0'
		self.icon = 'nsZip.png'
		root = FloatLayout()
		with open(getGuiPath('shaders/plasma.shader')) as stream:
			plasma_shader = stream.read()
			root.add_widget(ShaderWidget(fs=plasma_shader))
		gameList = GameList()
		self.rootWidget = RootWidget(gameList)
		root.add_widget(self.rootWidget)
		self.settings_cls = MySettingsWithTabbedPanel
		return root

	def build_config(self, config):
		config.setdefaults(
		'Settings', {
			'level': '[Lv. 22] Ultra (default)',
			'block': False,
			'solid': False,
			'bs': "1 MB (default)",
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
		settings.register_type('scrolloptions', SettingScrollOptions)
		settings.add_json_panel('Settings', self.config, getGuiPath('json/settings_basic.json'))
		settings.add_json_panel('Advanced', self.config, getGuiPath('json/settings_advanced.json'))
		settings.add_json_panel('Tools', self.config, getGuiPath('json/settings_tools.json'))

	def on_config_change(self, config, section, key, value):
		Logger.info("main.py: App.on_config_change: {0}, {1}, {2}, {3}".format(
			config, section, key, value))

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
	def __init__(self, config, rootWidget):
		level_scrolloptions = {
			"[Lv. 01] Debugging": 0,
			"[Lv. 08] Faster": 8,
			"[Lv. 12] Fast": 12,
			"[Lv. 14] Normal": 14,
			"[Lv. 18] Great": 18,
			"[Lv. 22] Ultra (default)": 22,
		}
		bs_scrolloptions = {
			"64 KB": 16,
			"128 KB": 17,
			"256 KB": 18,
			"512 KB": 19,
			"1 MB (default)": 20,
			"2 MB": 21,
			"4 MB": 22,
			"8 MB": 23,
			"16 MB": 24,
		}
		self.file = rootWidget.pathlist
		self.C = True if rootWidget.C is True else None
		self.D = True if rootWidget.D is True else None
		self.output = rootWidget.output
		self.info = True if rootWidget.info is True else None
		self.extract = True if rootWidget.extract is True else None
		self.create = True if rootWidget.create is True else None
		self.level = level_scrolloptions.get(config.get('Settings', 'level'), 22)
		self.block = True if config.get('Settings', 'block') is True else None
		self.solid = True if config.get('Settings', 'solid') is True else None
		self.bs = bs_scrolloptions.get(config.get('Settings', 'bs'), 20)
		self.verify = True if config.get('Settings', 'verify') is True else None
		self.threads = int(config.get('Advanced', 'threads'))
		self.parseCnmt = True if config.get('Advanced', 'parseCnmt') is True else None
		self.overwrite = True if config.get('Advanced', 'overwrite') is True else None
		self.rm_old_version = True if config.get('Advanced', 'rm_old_version') is True else None
		self.rm_source = True if config.get('Advanced', 'rm_source') is True else None
		self.depth = int(config.get('Tools', 'depth'))


if __name__ == '__main__':
	GUI().run()
