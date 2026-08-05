# coding=utf-8
"""Safe Translations Test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""

__author__ = 'ismailsunni@yahoo.co.id'
__date__ = '12/10/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')
import unittest
import os

from .qgis_stubs import ensure_qgis_app, qgis_available

QGIS_AVAILABLE = qgis_available()

if QGIS_AVAILABLE:
    ensure_qgis_app()

TRANSLATION_FILE = os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.pardir, 'i18n', 'af.qm'))


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
@unittest.skipUnless(os.path.exists(TRANSLATION_FILE),
                     'compiled translation i18n/af.qm not present')
class SafeTranslationsTest(unittest.TestCase):
    """Test translations work."""

    def setUp(self):
        """Runs before each test."""
        if 'LANG' in iter(os.environ.keys()):
            os.environ.__delitem__('LANG')

    def tearDown(self):
        """Runs after each test."""
        if 'LANG' in iter(os.environ.keys()):
            os.environ.__delitem__('LANG')

    def test_qgis_translations(self):
        """Test that translations work."""
        from qgis.PyQt.QtCore import QCoreApplication, QTranslator

        translator = QTranslator()
        translator.load(TRANSLATION_FILE)
        QCoreApplication.installTranslator(translator)

        expected_message = 'Goeie more'
        real_message = QCoreApplication.translate("@default", 'Good morning')
        self.assertEqual(real_message, expected_message)


if __name__ == "__main__":
    unittest.main()
