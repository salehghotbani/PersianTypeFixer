import unittest
from unittest.mock import patch

from startup import StartupPreference, VALUE_NAME


class StartupTests(unittest.TestCase):
    def test_missing_preference_is_disabled(self):
        with patch('startup.winreg.OpenKey', side_effect=FileNotFoundError):
            self.assertFalse(StartupPreference().is_enabled())

    def test_enable_writes_current_user_command(self):
        with patch('startup.winreg.CreateKeyEx') as create, \
                patch('startup.winreg.SetValueEx') as write, \
                patch('startup.startup_command', return_value='"C:\\Program Files\\Fixer.exe"'):
            StartupPreference().set_enabled(True)
            self.assertEqual(write.call_args.args[1], VALUE_NAME)
            self.assertEqual(write.call_args.args[-1], '"C:\\Program Files\\Fixer.exe"')
            self.assertTrue(create.called)

    def test_disable_removes_only_our_value(self):
        with patch('startup.winreg.OpenKey'), patch('startup.winreg.DeleteValue') as delete:
            StartupPreference().set_enabled(False)
            self.assertEqual(delete.call_args.args[1], VALUE_NAME)

    def test_disable_missing_value_is_harmless(self):
        with patch('startup.winreg.OpenKey', side_effect=FileNotFoundError):
            StartupPreference().set_enabled(False)

    def test_long_command_is_rejected_before_registry_change(self):
        with patch('startup.startup_command', return_value='x' * 261), \
                patch('startup.winreg.CreateKeyEx') as create:
            with self.assertRaises(OSError):
                StartupPreference().set_enabled(True)
            create.assert_not_called()
