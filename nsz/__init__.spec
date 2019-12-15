# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['__init__.py'],
             pathex=['C:\\Users\\Administrator\\Documents\\nsz\\nsz'],
             binaries=[],
             datas=[
             ('gui/json/*.json', 'nsz/gui/json'),
             ('gui/layout/*.kv', 'nsz/gui/layout'),
             ('gui/shaders/*.shader', 'nsz/gui/shaders'),
             ('gui/txt/*.txt', 'nsz/gui/txt'),
             ('gui/ico/*.ico', 'nsz/gui/ico')],
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
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='__init__')
