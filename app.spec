# -*- mode: python ; coding: utf-8 -*-

# Run: pyinstaller --hiddenimport=flask --hiddenimport=flask.render_template --hiddenimport=flast.send_file --hiddenimport=flask.Flask --hiddenimport=flask.request --hiddenimport=pptx --add-data ".env;." --add-data "templates;templates"  --add-data "static;static" app.py


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('templates', 'templates'), ('static', 'static')],
    hiddenimports=['flask', 'flask.render_template', 'flast.send_file', 'flask.Flask', 'flask.request', 'pptx'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='app',
)
