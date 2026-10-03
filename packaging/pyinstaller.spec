# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for FP&A Month-End Copilot per ADR-001 and ADR-005."""

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# Collect hidden imports required by FastAPI, uvicorn, and duckdb
hidden_imports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'pydantic',
    'duckdb',
    'polars',
    'openpyxl',
    'pptx',
    'httpx',
    'clr_loader',
    'pythonnet',
]

# Static assets from app/static (Vite build output)
datas = [
    ('../app/static', 'app/static'),
]

# Excluded packages to control bundle size per NFR-006 (<= 500 MB).
#
# Doc 15 section 3.4: "the excludes list carries a comment per entry naming what
# pulled the module in and why it is safe to drop. An unexplained exclude is a
# review failure." Every entry below therefore records its pull reason, measured
# against PyInstaller's own dependency graph (xref) from a scratch analysis with
# `excludes` emptied, then confirmed by a runtime import check in a clean
# subprocess. See CHANGELOG [Unreleased] for the recorded interpretation of the
# defensive entries.
excludes = [
    # tkinter - DEFENSIVE, NEVER IMPORTED. Nothing in the dependency graph pulls
    # tkinter in; a runtime import of the app's own modules does not load it
    # either. Kept as a guard so a future dependency cannot silently add a GUI
    # toolkit to the payload. Safe to drop: unused.
    'tkinter',

    # pandas - pulled in by duckdb.experimental.spark.sql.session (the Spark SQL
    # shim), polars._dependencies, and polars._utils.construction.utils - never
    # by application code. Verified: zero `pandas` references anywhere in app/
    # or scripts/, and importing the app's modules does not load pandas. This is
    # ~12.9 MB of the payload. Dropping it also removes the need for the
    # matplotlib and scipy excludes below, which pandas alone pulled in.
    'pandas',
    # pandas.libs - the native companion of pandas above; same reason.
    'pandas.libs',

    # matplotlib - TRANSITIVE FROM PANDAS, via pandas.plotting._core
    # (<- pandas.core.config_init <- pandas.core). No application code imports
    # it. Kept because it is a documented safety net for the pandas path and
    # costs nothing once pandas is excluded. Safe to drop: unused.
    'matplotlib',

    # scipy - TRANSITIVE FROM PANDAS, via pandas.core.dtypes.common and
    # pandas.core.missing. No application code imports it. Same reasoning as
    # matplotlib. Safe to drop: unused.
    'scipy',

    # IPython - pulled in by BOTH pandas.io.formats.printing AND
    # polars._utils.various (<- polars._dependencies). The polars edge survives
    # the removal of pandas, so this exclude is still required and is NOT merely
    # transitive-from-pandas. Safe to drop: not loaded by the app at runtime.
    'IPython',

    # jupyter - DEFENSIVE, NEVER IMPORTED. No import edge for `jupyter` exists
    # anywhere in the dependency graph. Kept as a guard against a notebook
    # dependency appearing via a transitive import. Safe to drop: unused.
    'jupyter',

    # tornado - pulled in by bottle, which is pulled in by webview.http
    # (<- webview <- app.desktop.shell <- app.desktop / main.py). Verified at
    # runtime: importing webview loads bottle WITHOUT loading tornado, because
    # pywebview uses bottle's WSGI reference server and not its Tornado server
    # adapter. Safe to drop on the observed path; note this is the one exclude
    # whose safety depends on pywebview's server choice, so re-check it if
    # pywebview is upgraded.
    'tornado',

    # sqlite3.test - DEFENSIVE, NOT REACHABLE. The stdlib sqlite3 package itself
    # IS required (it is the project's metadata store) and ships; only the test
    # submodule is excluded. Verified effective: the bundle contains sqlite3,
    # sqlite3.__main__, sqlite3.dbapi2 and sqlite3.dump, and not
    # sqlite3.test. Safe to drop: never imported by application code.
    'sqlite3.test',
]

a = Analysis(
    ['../app/cli/main.py'],
    pathex=['..'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FPandAMonthEndCopilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed desktop application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FPandAMonthEndCopilot',
)
