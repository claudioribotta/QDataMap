# coding=utf-8
"""Tests for the pinned-dependency verification (Section 4 of the v1.1 plan).

Runnable without QGIS: the qgis modules are stubbed by qgis_stubs.
"""

import importlib.metadata
import os
import unittest
from unittest.mock import MagicMock, patch

from .qgis_stubs import PLUGIN_DIR, load_plugin_module, make_plugin_instance

qdatamap = load_plugin_module()


class TestCheckPackage(unittest.TestCase):

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)

    def test_ok_when_version_matches_pin(self):
        with patch('importlib.util.find_spec', return_value=object()), \
             patch('importlib.metadata.version', return_value='2.3.1'):
            state, found, expected = self.plugin.check_package('pandas')
        self.assertEqual(state, 'ok')
        self.assertEqual(found, '2.3.1')
        self.assertEqual(expected, '2.3.1')

    def test_missing_when_find_spec_is_none(self):
        with patch('importlib.util.find_spec', return_value=None):
            state, found, expected = self.plugin.check_package('pandas')
        self.assertEqual(state, 'missing')
        self.assertIsNone(found)
        self.assertEqual(expected, '2.3.1')

    def test_mismatch_on_different_version(self):
        with patch('importlib.util.find_spec', return_value=object()), \
             patch('importlib.metadata.version', return_value='3.5.0'):
            state, found, expected = self.plugin.check_package('matplotlib')
        self.assertEqual(state, 'mismatch')
        self.assertEqual(found, '3.5.0')
        self.assertEqual(expected, '3.10.0')

    def test_mismatch_unknown_on_package_not_found_error(self):
        with patch('importlib.util.find_spec', return_value=object()), \
             patch('importlib.metadata.version',
                   side_effect=importlib.metadata.PackageNotFoundError('seaborn')):
            state, found, expected = self.plugin.check_package('seaborn')
        self.assertEqual(state, 'mismatch')
        self.assertEqual(found, 'unknown')
        self.assertEqual(expected, '0.13.2')


class TestPinnedDependencies(unittest.TestCase):

    def test_five_packages_pinned(self):
        self.assertEqual(len(qdatamap.PINNED_DEPENDENCIES), 5)

    def test_pins_match_requirements_txt(self):
        requirements_path = os.path.join(PLUGIN_DIR, 'requirements.txt')
        pins = {}
        with open(requirements_path, encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                package, version = line.split('==')
                pins[package] = version
        self.assertEqual(pins, qdatamap.PINNED_DEPENDENCIES)


class TestInstallPackage(unittest.TestCase):

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)

    def _run_install(self, **kwargs):
        completed = MagicMock(returncode=0, stderr='')
        with patch.object(qdatamap.subprocess, 'run', return_value=completed) as run_mock:
            result = self.plugin.install_package('pandas', **kwargs)
        self.assertTrue(result)
        args, call_kwargs = run_mock.call_args
        return args[0], call_kwargs

    def test_command_uses_exact_version_specifier(self):
        command, kwargs = self._run_install()
        self.assertIn('pandas==2.3.1', command)
        self.assertNotIn('--upgrade', command)
        self.assertEqual(kwargs.get('timeout'), 300)

    def test_upgrade_flag_only_in_mismatch_case(self):
        command, _ = self._run_install(upgrade=True)
        self.assertIn('--upgrade', command)
        self.assertIn('pandas==2.3.1', command)
        # --upgrade must precede the requirement specifier
        self.assertLess(command.index('--upgrade'), command.index('pandas==2.3.1'))


class TestNoInstallWithoutConfirmation(unittest.TestCase):
    """No code path may invoke install_package() without user confirmation."""

    def setUp(self):
        self.plugin = make_plugin_instance(qdatamap)
        self.plugin.install_package = MagicMock(name='install_package', return_value=True)

    def test_missing_declined_never_installs(self):
        with patch.object(qdatamap, 'QMessageBox') as box:
            box.question.return_value = box.No
            with patch.object(self.plugin, 'check_package',
                              return_value=('missing', None, '2.3.1')):
                result = self.plugin.check_and_install_dependencies()
        self.assertFalse(result)
        self.plugin.install_package.assert_not_called()
        # The confirmation dialog was actually raised before any install
        box.question.assert_called_once()

    def test_missing_dialog_lists_exact_versions(self):
        with patch.object(qdatamap, 'QMessageBox') as box:
            box.question.return_value = box.No
            with patch.object(self.plugin, 'check_package',
                              return_value=('missing', None, 'x')):
                self.plugin.check_and_install_dependencies()
        message = box.question.call_args[0][2]
        for package, version in qdatamap.PINNED_DEPENDENCIES.items():
            self.assertIn(f'{package}=={version}', message)

    def test_missing_accepted_installs_after_confirmation(self):
        with patch.object(qdatamap, 'QMessageBox') as box:
            box.question.return_value = box.Yes
            with patch.object(self.plugin, 'check_package',
                              return_value=('missing', None, 'x')):
                result = self.plugin.check_and_install_dependencies()
        self.assertTrue(result)
        self.assertEqual(self.plugin.install_package.call_count,
                         len(qdatamap.PINNED_DEPENDENCIES))
        # No --upgrade path for missing packages
        for call in self.plugin.install_package.call_args_list:
            self.assertNotIn('upgrade', call.kwargs)

    def _mismatch_dialog(self, clicked_index):
        """Run the mismatch flow clicking the button at clicked_index
        (0 = install pinned, 1 = continue anyway, 2 = cancel)."""
        with patch.object(qdatamap, 'QMessageBox') as box:
            instance = box.return_value
            buttons = [MagicMock(name=f'button{i}') for i in range(3)]
            instance.addButton.side_effect = buttons
            instance.clickedButton.return_value = buttons[clicked_index]
            with patch.object(self.plugin, 'check_package',
                              return_value=('mismatch', '1.0.0', '2.3.1')):
                result = self.plugin.check_and_install_dependencies()
        return result, instance

    def test_mismatch_cancel_never_installs(self):
        result, _ = self._mismatch_dialog(clicked_index=2)
        self.assertFalse(result)
        self.plugin.install_package.assert_not_called()

    def test_mismatch_continue_anyway_never_installs(self):
        result, _ = self._mismatch_dialog(clicked_index=1)
        self.assertTrue(result)
        self.plugin.install_package.assert_not_called()

    def test_mismatch_install_uses_upgrade(self):
        result, instance = self._mismatch_dialog(clicked_index=0)
        self.assertTrue(result)
        self.assertEqual(self.plugin.install_package.call_count,
                         len(qdatamap.PINNED_DEPENDENCIES))
        for call in self.plugin.install_package.call_args_list:
            self.assertTrue(call.kwargs.get('upgrade'))
        # The dialog was raised (three buttons added) before installing
        self.assertEqual(instance.addButton.call_count, 3)

    def test_all_ok_no_dialog_no_install(self):
        with patch.object(qdatamap, 'QMessageBox') as box:
            with patch.object(self.plugin, 'check_package',
                              return_value=('ok', '1.0', '1.0')):
                result = self.plugin.check_and_install_dependencies()
        self.assertTrue(result)
        self.plugin.install_package.assert_not_called()
        box.question.assert_not_called()
        box.assert_not_called()


if __name__ == '__main__':
    unittest.main()
