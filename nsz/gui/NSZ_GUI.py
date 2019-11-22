from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory
from ShaderWidget import *
from RootWidget import *
from GameList import *
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
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
		return root

if __name__ == '__main__':
	GUI().run()
