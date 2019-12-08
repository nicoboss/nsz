from kivy.uix.settings import *
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.metrics import *
from kivy.uix.togglebutton import *
from kivy.uix.button import Button

class SettingScrollOptions(SettingOptions):

	def _create_popup(self, instance):
		
		content = GridLayout(cols=1, spacing='10dp')
		scrollview = ScrollView(do_scroll_x=False, size_hint=(1, 0.85))
		scrollcontent = StackLayout(size_hint=(1, None), spacing='5dp')
		scrollcontent.bind(minimum_height=scrollcontent.setter('height'))
		self.popup = popup = Popup(content=content, title=self.title, size_hint=(0.5, 0.9),  auto_dismiss=False)
		popup.open()
		
		content.add_widget(Widget(size_hint_y=None, height=dp(2)))
		uid = str(self.uid)
		for option in self.options:
			state = 'down' if option == self.value else 'normal'
			btn = ToggleButton(text=option, state=state, group=uid, height=dp(50), size_hint=(1, None))
			btn.bind(on_release=self._set_option)
			scrollcontent.add_widget(btn)

		scrollview.add_widget(scrollcontent)
		content.add_widget(scrollview)
		btn = Button(text='Cancel', height=dp(50), size_hint=(1, None))
		btn.bind(on_release=popup.dismiss)
		content.add_widget(btn)
