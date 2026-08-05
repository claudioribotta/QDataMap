# coding=utf-8
"""Tests for compute_join_stats() and the behaviour-invariance of
preliminary_join_stats() (Section 6.3 of the v1.1 plan).

These tests require a QGIS environment (QgsVectorLayer, ogr/delimitedtext
providers) and are skipped when it is not importable.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from .qgis_stubs import (ensure_qgis_app, load_plugin_module,
                         make_plugin_instance, qgis_available)

QGIS_AVAILABLE = qgis_available()

if QGIS_AVAILABLE:
    QGIS_APP = ensure_qgis_app()

qdatamap = load_plugin_module()


def make_fixtures(tmpdir, csv_rows, gpkg_keys=('A', 'B', 'C', 'D')):
    """Create a GeoPackage with known keys and a CSV with the given rows."""
    from qgis.core import (QgsVectorLayer, QgsFeature, QgsGeometry,
                          QgsVectorFileWriter, QgsRectangle,
                          QgsCoordinateTransformContext)

    layer = QgsVectorLayer('Polygon?crs=EPSG:4326&field=key:string', 'fixture', 'memory')
    provider = layer.dataProvider()
    features = []
    for i, key in enumerate(gpkg_keys):
        feature = QgsFeature(layer.fields())
        feature.setAttribute('key', key)
        feature.setGeometry(QgsGeometry.fromRect(QgsRectangle(i, 0, i + 0.9, 1)))
        features.append(feature)
    provider.addFeatures(features)

    gpkg_path = os.path.join(tmpdir, 'fixture.gpkg')
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = 'GPKG'
    QgsVectorFileWriter.writeAsVectorFormatV3(
        layer, gpkg_path, QgsCoordinateTransformContext(), options)

    csv_path = os.path.join(tmpdir, 'fixture.csv')
    with open(csv_path, 'w', encoding='utf-8', newline='') as handle:
        handle.write('key,value\n')
        for key, value in csv_rows:
            handle.write(f'{key},{value}\n')
    # Forward slashes, as produced by the Qt file dialogs the plugin uses:
    # the delimitedtext file:/// URI does not accept backslashes
    return gpkg_path.replace('\\', '/'), csv_path.replace('\\', '/')


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
class TestComputeJoinStats(unittest.TestCase):

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)
        self.tmpdir = tempfile.mkdtemp()

    def compute(self, csv_rows, gpkg_keys=('A', 'B', 'C', 'D')):
        gpkg, csv_path = make_fixtures(self.tmpdir, csv_rows, gpkg_keys)
        return self.plugin.compute_join_stats(gpkg, 'key', csv_path, 'key')

    def test_partial_match_with_duplicates(self):
        # A matches twice (duplicate), B once, X never
        stats = self.compute([('A', 1), ('A', 2), ('B', 3), ('X', 4)])
        self.assertEqual(stats['input1_count'], 4)
        self.assertEqual(stats['input2_count'], 4)
        self.assertEqual(stats['matched_unique_input1'], 2)
        self.assertEqual(stats['unmatched_input1'], 2)
        self.assertEqual(stats['matched_input2'], 3)
        self.assertEqual(stats['unmatched_input2'], 1)
        self.assertEqual(stats['total_matches'], 3)
        self.assertEqual(stats['duplicate_geometries'], 1)

    def test_no_match(self):
        stats = self.compute([('X', 1), ('Y', 2)])
        self.assertEqual(stats['matched_unique_input1'], 0)
        self.assertEqual(stats['unmatched_input1'], 4)
        self.assertEqual(stats['matched_input2'], 0)
        self.assertEqual(stats['unmatched_input2'], 2)
        self.assertEqual(stats['total_matches'], 0)
        self.assertEqual(stats['duplicate_geometries'], 0)

    def test_all_match(self):
        stats = self.compute([('A', 1), ('B', 2), ('C', 3), ('D', 4)])
        self.assertEqual(stats['matched_unique_input1'], 4)
        self.assertEqual(stats['unmatched_input1'], 0)
        self.assertEqual(stats['unmatched_input2'], 0)
        self.assertEqual(stats['total_matches'], 4)
        self.assertEqual(stats['duplicate_geometries'], 0)

    def test_input_vertex_count(self):
        # 4 rectangular polygons, closed ring of 5 vertices each
        stats = self.compute([('A', 1)])
        self.assertEqual(stats['input1_vertex_count'], 20)

    def test_duplicate_csv_keys(self):
        stats = self.compute([('A', 1), ('A', 2), ('A', 3)])
        self.assertEqual(stats['matched_unique_input1'], 1)
        self.assertEqual(stats['total_matches'], 3)
        self.assertEqual(stats['duplicate_geometries'], 2)

    def test_empty_csv(self):
        stats = self.compute([])
        self.assertEqual(stats['input2_count'], 0)
        self.assertEqual(stats['total_matches'], 0)
        self.assertEqual(stats['matched_unique_input1'], 0)
        self.assertEqual(stats['unmatched_input1'], 4)
        self.assertEqual(stats['duplicate_geometries'], 0)


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
class TestPreliminaryJoinStatsInvariance(unittest.TestCase):
    """preliminary_join_stats() must show the same dialog sequence and return
    the same True/False as v1.0 in the same scenarios."""

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)
        self.plugin.ask_user_confirmation = MagicMock(return_value=True)
        self.tmpdir = tempfile.mkdtemp()

    def run_prelim(self, csv_rows, information_response='Ok'):
        gpkg, csv_path = make_fixtures(self.tmpdir, csv_rows)
        with patch.object(qdatamap, 'QMessageBox') as box:
            box.information.return_value = getattr(box, information_response)
            result = self.plugin.preliminary_join_stats(gpkg, 'key', csv_path, 'key')
            info_calls = box.information.call_count
        return result, info_calls

    def test_cancel_returns_false_without_confirmations(self):
        result, info_calls = self.run_prelim(
            [('A', 1)], information_response='Cancel')
        self.assertFalse(result)
        self.assertEqual(info_calls, 1)
        self.plugin.ask_user_confirmation.assert_not_called()

    def test_clean_join_single_dialog_returns_true(self):
        # All matched on both sides: no warning dialogs at all
        result, info_calls = self.run_prelim(
            [('A', 1), ('B', 2), ('C', 3), ('D', 4)])
        self.assertTrue(result)
        self.assertEqual(info_calls, 1)
        self.plugin.ask_user_confirmation.assert_not_called()

    def test_warning_sequence_for_duplicates_and_unmatched(self):
        # duplicates + unmatched csv + unmatched shape: three confirmations,
        # in this order
        result, _ = self.run_prelim([('A', 1), ('A', 2), ('X', 3)])
        self.assertTrue(result)
        warnings = [call.args[1] for call in
                    self.plugin.ask_user_confirmation.call_args_list]
        self.assertEqual(len(warnings), 3)
        self.assertIn('duplicated', warnings[0])
        self.assertIn('tabular dataset will be discarded', warnings[1])
        self.assertIn('geospatial input will be discarded', warnings[2])

    def test_declined_warning_returns_false(self):
        self.plugin.ask_user_confirmation = MagicMock(return_value=False)
        result, _ = self.run_prelim([('A', 1), ('A', 2)])
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
