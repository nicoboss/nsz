from kivy.clock import Clock
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import RenderContext
from kivy.properties import StringProperty

class ShaderWidget(FloatLayout):

	# property to set the source code for fragment shader
	fs = StringProperty(None)

	def __init__(self, **kwargs):
		# Instead of using Canvas, we will use a RenderContext,
		# and change the default shader used.
		self.canvas = RenderContext()

		# call the constructor of parent
		# if they are any graphics object, they will be added on our new canvas
		super(ShaderWidget, self).__init__(**kwargs)

		# We'll update our glsl variables in a clock
		Clock.schedule_interval(self.update_glsl, 1 / 60.)

	def on_fs(self, instance, value):
		# set the fragment shader to our source code
		shader = self.canvas.shader
		old_value = shader.fs
		shader.fs = value
		if not shader.success:
			shader.fs = old_value
			raise Exception('failed')

	def update_glsl(self, *largs):
		self.canvas['time'] = Clock.get_boottime()
		self.canvas['resolution'] = list(map(float, self.size))
		# This is needed for the default vertex shader.
		win_rc = Window.render_context
		self.canvas['projection_mat'] = win_rc['projection_mat']
		self.canvas['modelview_mat'] = win_rc['modelview_mat']
		self.canvas['frag_modelview_mat'] = win_rc['frag_modelview_mat']
