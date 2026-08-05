# coding=utf-8
"""Resources test.

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
class QDataMapResourcesTest(unittest.TestCase):
    """Test resources work."""

    def test_icon_png(self):
        """The plugin icon is registered in the compiled Qt resources."""
        from qgis.PyQt.QtGui import QIcon
        from qgis.PyQt.QtCore import QFile
        from .. import resources  # noqa: F401  # registers the resources

        # Prefix as declared in resources.qrc
        path = ':/plugins/qgis_data_mapping/icon.png'
        self.assertTrue(QFile.exists(path))
        icon = QIcon(path)
        self.assertFalse(icon.isNull())


if __name__ == "__main__":
    unittest.main()
