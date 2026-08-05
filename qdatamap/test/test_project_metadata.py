# coding=utf-8
"""Tests for record_environment_metadata() (Section 5 of the v1.1 plan).

These tests require a QGIS environment (QgsProject) and are skipped when it
is not importable.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from .qgis_stubs import (ensure_qgis_app, load_plugin_module,
                         make_plugin_instance, qgis_available)

QGIS_AVAILABLE = qgis_available()

if QGIS_AVAILABLE:
    QGIS_APP = ensure_qgis_app()

qdatamap = load_plugin_module()

EXPECTED_KEYS = ('plugin_version', 'qgis_version', 'qgis_ltr_target',
                 'dependencies', 'dependencies_pinned', 'environment_matches_pin')


@unittest.skipUnless(QGIS_AVAILABLE, 'QGIS environment required')
class TestRecordEnvironmentMetadata(unittest.TestCase):

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)

    def read_entry(self, key):
        from qgis.core import QgsProject
        value, ok = QgsProject.instance().readEntry('QDataMap', key)
        return value, ok

    def test_all_expected_keys_written(self):
        self.plugin.record_environment_metadata()
        for key in EXPECTED_KEYS:
            value, ok = self.read_entry(key)
            self.assertTrue(ok, f'entry not written: {key}')
            self.assertNotEqual(value, '', f'empty entry: {key}')

    def test_values_are_consistent(self):
        from qgis.core import Qgis
        self.plugin.record_environment_metadata()
        self.assertEqual(self.read_entry('plugin_version')[0],
                         qdatamap.QDATAMAP_VERSION)
        self.assertEqual(self.read_entry('qgis_ltr_target')[0],
                         qdatamap.QGIS_LTR_TARGET)
        self.assertEqual(self.read_entry('qgis_version')[0], Qgis.QGIS_VERSION)
        pinned = json.loads(self.read_entry('dependencies_pinned')[0])
        self.assertEqual(pinned, qdatamap.PINNED_DEPENDENCIES)
        resolved = json.loads(self.read_entry('dependencies')[0])
        self.assertEqual(sorted(resolved.keys()),
                         sorted(qdatamap.PINNED_DEPENDENCIES.keys()))

    def test_matches_pin_false_when_a_version_differs(self):
        drifted = dict(qdatamap.PINNED_DEPENDENCIES)
        drifted['pandas'] = '1.5.0'
        with patch.object(self.plugin, 'resolved_dependency_versions',
                          return_value=drifted):
            self.plugin.record_environment_metadata()
        self.assertEqual(self.read_entry('environment_matches_pin')[0], 'false')
        resolved = json.loads(self.read_entry('dependencies')[0])
        self.assertEqual(resolved['pandas'], '1.5.0')

    def test_matches_pin_true_when_all_versions_match(self):
        with patch.object(self.plugin, 'resolved_dependency_versions',
                          return_value=dict(qdatamap.PINNED_DEPENDENCIES)):
            self.plugin.record_environment_metadata()
        self.assertEqual(self.read_entry('environment_matches_pin')[0], 'true')

    def test_write_error_does_not_propagate(self):
        broken_project = MagicMock()
        broken_project.instance.side_effect = RuntimeError('simulated failure')
        with patch.object(qdatamap, 'QgsProject', broken_project):
            # Must not raise: in batch mode an exception here would stop
            # the whole series
            self.plugin.record_environment_metadata()


if __name__ == '__main__':
    unittest.main()
