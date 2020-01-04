#Source: https://github.com/JakubBlaha/KivyOnTop/blob/master/KivyOnTop/__init__.py
#Commit: 492f39005867c485b08042b9d68589088cffd786
#Author: Jakub Bláha
#License: MIT

name = "KivyOnTop"

import win32gui
import win32con


def find_hwnd(title: str):
	global hwnd
	hwnd = win32gui.FindWindow(None, title)

	return hwnd


def set_always_on_top(title: str):
	'''
	Sets the HWND_TOPMOST flag for the current Kivy Window.
	This behavior will be overwritten by setting position of the window from kivy.
	If you want the window to stay on top of others even after changing the position or size from kivy, 
	use the register_topmost function instead.
	'''

	global hwnd

	if not 'hwnd' in globals():
		find_hwnd(title)

	rect = win32gui.GetWindowRect(hwnd)
	x = rect[0]
	y = rect[1]
	w = rect[2] - x
	h = rect[3] - y

	win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, w, h, 0)


def set_not_always_on_top(title: str):
	'''
	Sets the HWND_NOTOPMOST flag for the current Kivy Window.
	'''

	global hwnd

	if not 'hwnd' in globals():
		find_hwnd(title)

	rect = win32gui.GetWindowRect(hwnd)
	x = rect[0]
	y = rect[1]
	w = rect[2] - x
	h = rect[3] - y

	win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, x, y, w, h, 0)


def register_topmost(Window, title: str):
	'''
	Makes the current Kivy Window stay always on top.
	'''

	Window.bind(on_draw=lambda *args: set_always_on_top(title))


def unregister_topmost(Window, title: str):
	'''
	Disabled the HWND_TOPMOST flag for the current Kivy Window.
	'''

	Window.unbind(on_draw=set_always_on_top)
	set_not_always_on_top(title)
