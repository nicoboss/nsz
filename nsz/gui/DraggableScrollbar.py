#!python
import kivy
kivy.require('1.5.1')
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.stacklayout import StackLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.recycleview import RecycleView
from kivy.uix.slider import Slider
from functools import partial

class DraggableScrollbar(GridLayout):
	slider = None

	def __init__(self, recycleView, **kwargs):
		
		# call the constructor of parent
		# if they are any graphics object, they will be added on our new canvas
		super(DraggableScrollbar, self).__init__(**kwargs)
		self.cols = 2
		self.orientation='lr-bt'

		#the last child of layout1 and this will act as the draggable scrollbar
		self.slider = Slider(min=0, max=1, value=25, orientation='vertical', step=0.01, size_hint=(0.03, 0.95))

		recycleView.bind(scroll_y=partial(self.slider_change))

		#what this does is, whenever the slider is dragged, it scrolls the previously added scrollview by the same amount the slider is dragged
		self.slider.bind(value=partial(self.scroll_change, recycleView))
		
		self.add_widget(recycleView)
		self.add_widget(self.slider)

	def scroll_change(self, recycleView, instance, value):
		recycleView.scroll_y = value

	def slider_change(self, instance, value):
		if value >= 0:
		#this to avoid 'maximum recursion depth exceeded' error
			self.slider.value=value
