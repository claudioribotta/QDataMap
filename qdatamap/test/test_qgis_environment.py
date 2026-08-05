# coding=utf-8
"""Tests for QGIS functionality.


.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'tim@linfiniti.com'
__date__ = '20/01/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import os
import unittest

from .qgis_stubs import ensure_qgis_app, qgis_available

QGIS_AVAILABLE = qgis_available()

if QGIS_AVAILABLE:
    QGIS_APP = ensure_qgis_app()


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
class QGISTest(unittest.TestCase):
    """Test the QGIS Environment"""

    def test_qgis_environment(self):
        """QGIS environment has the providers the plugin relies on."""
        from qgis.core import QgsProviderRegistry

        r = QgsProviderRegistry.instance()
        self.assertIn('gdal', r.providerList())
        self.assertIn('ogr', r.providerList())
        self.assertIn('delimitedtext', r.providerList())

    def test_projection(self):
        """Test that QGIS properly parses a wkt string.
        """
        from qgis.core import QgsCoordinateReferenceSystem, QgsRasterLayer

        crs = QgsCoordinateReferenceSystem()
        wkt = (
            'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
            'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
            'PRIMEM["Greenwich",0.0],UNIT["Degree",'
            '0.0174532925199433]]')
        crs.createFromWkt(wkt)
        auth_id = crs.authid()
        expected_auth_id = 'EPSG:4326'
        self.assertEqual(auth_id, expected_auth_id)

        # now test for a loaded layer; recent GDAL releases identify the
        # fixture's WGS84 WKT as OGC:CRS84 (axis order variant of EPSG:4326)
        path = os.path.join(os.path.dirname(__file__), 'tenbytenraster.asc')
        title = 'TestRaster'
        layer = QgsRasterLayer(path, title)
        auth_id = layer.crs().authid()
        self.assertIn(auth_id, ('EPSG:4326', 'OGC:CRS84'))


if __name__ == '__main__':
    unittest.main()
