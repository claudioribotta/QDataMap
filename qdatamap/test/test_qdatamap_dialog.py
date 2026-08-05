# coding=utf-8
"""Dialog test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'claudio.ribotta@outlook.com'
__date__ = '2025-02-25'
__copyright__ = 'Copyright 2025, claudio.ribotta'

import unittest

from .qgis_stubs import ensure_qgis_app, qgis_available

QGIS_AVAILABLE = qgis_available()

if QGIS_AVAILABLE:
    ensure_qgis_app()


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
class QDataMapDialogTest(unittest.TestCase):
    """Test that the plugin dialog can be built from the shipped .ui file."""

    def setUp(self):
        """Runs before each test."""
        from ..qdatamap_dialog import qdatamapdialog
        self.dialog = qdatamapdialog(None)

    def tearDown(self):
        """Runs after each test."""
        self.dialog = None

    def test_dialog_has_all_value_widgets(self):
        """Every value widget dumped by collect_ui_configuration() exists."""
        import os
        import xml.etree.ElementTree as ET
        from .qgis_stubs import PLUGIN_DIR
        from ..qdatamap import VALUE_WIDGET_CLASSES

        ui_path = os.path.join(PLUGIN_DIR, 'qdatamap_dialog_base.ui')
        root = ET.parse(ui_path).getroot()
        for node in root.iter('widget'):
            if node.get('class') in VALUE_WIDGET_CLASSES:
                name = node.get('name')
                self.assertTrue(hasattr(self.dialog, name),
                                f'widget missing on dialog: {name}')


if __name__ == "__main__":
    unittest.main()
