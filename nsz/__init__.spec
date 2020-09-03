# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['__init__.py'],
             pathex=['C:\\Users\\nico\\Documents\\GitHub\\nsz\\nsz'],
             binaries=[],
             datas=[
             ('gui/fonts/*.*', 'nsz/gui/fonts'),
             ('gui/json/*.json', 'nsz/gui/json'),
             ('gui/layout/*.kv', 'nsz/gui/layout'),
             ('gui/shaders/*.shader', 'nsz/gui/shaders'),
             ('gui/txt/*.txt', 'nsz/gui/txt'),
             ('gui/nsZip.png', 'nsz/gui'),
             ('C:/Python37/share/sdl2/bin/libpng16-16.dll', '.'),
             ('C:/Python37/share/sdl2/bin/LICENSE.png.txt', '.'),
             ('C:/Python37/Lib/site-packages/ansicon/ANSI64.dll', 'ansicon')],
             hiddenimports=['win32timezone', 'pyexpat', 'pkg_resources.py2_warn', 'pycryptodome>=3.9.0', 'pycparser', 'cffi', 'zstandard', 'six', 'ansicon', 'jinxed', 'wcwidth', 'blessed', 'enlighten', 'enchant', 'pywin32', 'pypiwin32' 'docutils', 'pygments', 'jinxed.terminfo.ansicon', 'jinxed.terminfo.vtwin10', 'jinxed.terminfo.xterm', 'jinxed.terminfo.xterm_256color', 'jinxed.terminfo.xterm_256colors'],
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
          console=True,
          icon='C:\\Users\\nico\\Documents\\GitHub\\nsz\\nsz\\nsZip.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='__init__')
