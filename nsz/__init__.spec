# -*- mode: python ; coding: utf-8 -*-

from kivy_deps import sdl2, glew
import cv2
import enchant
block_cipher = None

a = Analysis(['__init__.py'],
             pathex=['C:\\Users\\Administrator\\Documents\\nsz\\nsz'],
             binaries=[],
             datas=[
             ('gui/json/*.json', 'nsz/gui/json'),
             ('gui/layout/*.kv', 'nsz/gui/layout'),
             ('gui/shaders/*.shader', 'nsz/gui/shaders'),
             ('gui/fonts/*', 'nsz/gui/fonts'),
             ('gui/txt/*.txt', 'nsz/gui/txt'),
             ('gui/nsZip.png', 'nsz/gui/nsZip.png')],
             hiddenimports=['win32timezone'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='nsz',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.scripts,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
               strip=False,
               upx=True,
               upx_exclude=[],
               name='__init__')
