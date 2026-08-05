# coding=utf-8
"""Import helper for tests that must run without a QGIS installation.

qdatamap.py imports qgis at module level. The tests of Section 8.1 of the
v1.1 revision plan (dependencies, resource monitor, report builders, UI
configuration) exercise logic that does not need QGIS at all, so this module
installs lightweight stand-ins for the qgis modules before importing the
plugin. When a real QGIS environment is available the plugin is imported
against it unchanged.
"""

import importlib
import os
import re
import sys
import types
from unittest.mock import MagicMock

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(TEST_DIR)
PARENT_DIR = os.path.dirname(PLUGIN_DIR)
PACKAGE_NAME = os.path.basename(PLUGIN_DIR)

_plugin_module = None
_qgis_app = None


def ensure_qgis_app():
    """Initialize a headless QgsApplication once and return it.

    The legacy get_qgis_app() helper in utilities.py depends on
    qgis_interface.py, which still uses the QGIS 2 API
    (QgsMapLayerRegistry, QgsMapCanvasLayer) and cannot be imported under
    QGIS 3. Data-provider registration (ogr, delimitedtext) only needs
    QgsApplication.initQgis(), which is all the v1.1 tests require.
    """
    global _qgis_app
    if _qgis_app is None:
        from qgis.core import QgsApplication
        _qgis_app = QgsApplication([], True)
        _qgis_app.initQgis()
    return _qgis_app


def qgis_available():
    """True when the real qgis package (not a test stub) can be imported."""
    try:
        import qgis.core
    except Exception:
        return False
    return not getattr(qgis.core, '__qdatamap_stub__', False)


def _make_stub(name, exports=()):
    module = types.ModuleType(name)
    module.__qdatamap_stub__ = True
    module.__all__ = [str(export) for export in exports]
    for export in exports:
        setattr(module, export, MagicMock(name=export))

    # PEP 562: any other attribute (explicit `from x import name`) resolves
    # to a fresh MagicMock instead of raising. Dunder names keep normal
    # module semantics (star-import reads __all__ through getattr).
    def module_getattr(attr, _name=name):
        if attr.startswith('__') and attr.endswith('__'):
            raise AttributeError(attr)
        return MagicMock(name=f'{_name}.{attr}')

    module.__getattr__ = module_getattr
    sys.modules[name] = module
    return module


def _install_stubs():
    # Names the plugin pulls in via `from qgis.core import *`: collect every
    # Qgs*/Qgis/NULL token actually used in the source so star-import works.
    source_path = os.path.join(PLUGIN_DIR, 'qdatamap.py')
    with open(source_path, encoding='utf-8') as handle:
        source = handle.read()
    star_names = set(re.findall(r'\b(?:Qgs\w+|Qgis|NULL)\b', source))

    qgis_module = _make_stub('qgis')
    core = _make_stub('qgis.core', star_names)
    gui = _make_stub('qgis.gui')
    gui.__all__ = []
    processing = _make_stub('qgis.processing')
    pyqt = _make_stub('qgis.PyQt')
    qtcore = _make_stub('qgis.PyQt.QtCore')
    qtgui = _make_stub('qgis.PyQt.QtGui')
    qtwidgets = _make_stub('qgis.PyQt.QtWidgets')

    qgis_module.core = core
    qgis_module.gui = gui
    qgis_module.processing = processing
    qgis_module.PyQt = pyqt
    pyqt.QtCore = qtcore
    pyqt.QtGui = qtgui
    pyqt.QtWidgets = qtwidgets

    # Compiled Qt resources and the dialog wrapper require PyQt at import
    # time: replace them with stubs so they are never executed.
    resources = types.ModuleType(f'{PACKAGE_NAME}.resources')
    resources.__all__ = []
    sys.modules[f'{PACKAGE_NAME}.resources'] = resources

    dialog = types.ModuleType(f'{PACKAGE_NAME}.qdatamap_dialog')
    dialog.qdatamapdialog = MagicMock(name='qdatamapdialog')
    sys.modules[f'{PACKAGE_NAME}.qdatamap_dialog'] = dialog


def load_plugin_module():
    """Import and return qdatamap.qdatamap, stubbing qgis when unavailable."""
    global _plugin_module
    if _plugin_module is not None:
        return _plugin_module

    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)

    if not qgis_available():
        _install_stubs()

    _plugin_module = importlib.import_module(f'{PACKAGE_NAME}.qdatamap')
    return _plugin_module


def make_plugin_instance(module):
    """Build a qdatamap_plugin instance without running its __init__.

    The constructor needs a live QGIS iface; the tested methods do not.
    """
    plugin = object.__new__(module.qdatamap_plugin)
    plugin.plugin_dir = PLUGIN_DIR
    plugin.iface = MagicMock(name='iface')
    plugin.dlg = MagicMock(name='dlg')
    plugin.csv_schema_validation = None
    plugin.last_run_metrics = None
    plugin._join_stats_cache = None
    return plugin
