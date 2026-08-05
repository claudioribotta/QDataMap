# coding=utf-8
"""Tests for collect_ui_configuration() (Section 6.1 of the v1.1 plan).

Runnable without QGIS: the dump is driven by parsing qdatamap_dialog_base.ui,
and widget values are read through the (possibly mocked) dialog attributes.
"""

import os
import unittest
import xml.etree.ElementTree as ET

from .qgis_stubs import PLUGIN_DIR, load_plugin_module, make_plugin_instance

qdatamap = load_plugin_module()

EXPECTED_PARAMETER_COUNT = 61


def value_widget_names_from_ui():
    """Parse the .ui file and return the objectNames of all value widgets.

    This is the reference the dump is checked against: if a widget is added,
    removed or renamed without updating the dump, this test fails loudly.
    """
    ui_path = os.path.join(PLUGIN_DIR, 'qdatamap_dialog_base.ui')
    root = ET.parse(ui_path).getroot()
    names = []
    for node in root.iter('widget'):
        if node.get('class') in qdatamap.VALUE_WIDGET_CLASSES:
            names.append(node.get('name'))
    return names


class TestCollectUiConfiguration(unittest.TestCase):

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)

    def test_returns_61_keys(self):
        config = self.plugin.collect_ui_configuration()
        self.assertEqual(len(config), EXPECTED_PARAMETER_COUNT)

    def test_keys_match_ui_file_exactly(self):
        config = self.plugin.collect_ui_configuration()
        expected = value_widget_names_from_ui()
        self.assertEqual(sorted(config.keys()), sorted(expected))

    def test_ui_file_itself_declares_61_value_widgets(self):
        # Guards the manuscript claim independently of the dump code.
        self.assertEqual(len(value_widget_names_from_ui()),
                         EXPECTED_PARAMETER_COUNT)

    def test_unreadable_widget_reports_none_not_exception(self):
        # A dialog missing one widget must produce a None value, not a crash.
        class Dialog:
            pass
        self.plugin.dlg = Dialog()  # no widget attributes at all
        config = self.plugin.collect_ui_configuration()
        self.assertEqual(len(config), EXPECTED_PARAMETER_COUNT)
        self.assertTrue(all(value is None for value in config.values()))


if __name__ == '__main__':
    unittest.main()
