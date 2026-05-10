import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import platform
import ssd_chrome_automator

class TestSSDAutomator(unittest.TestCase):

    @patch('psutil.disk_partitions')
    def test_find_target_ssd_found_linux(self, mock_partitions):
        mock_p = MagicMock()
        mock_p.mountpoint = '/media/user/WD SA500'
        mock_p.device = '/dev/sdb1'
        mock_partitions.return_value = [mock_p]
        
        with patch('platform.system', return_value='Linux'):
            path = ssd_chrome_automator.find_target_ssd(['WD SA500'])
            self.assertEqual(path, '/media/user/WD SA500')

    @patch('ssd_chrome_automator.get_windows_volume_label')
    @patch('psutil.disk_partitions')
    @patch('platform.system')
    def test_find_target_ssd_found_windows(self, mock_system, mock_partitions, mock_label):
        mock_system.return_value = 'Windows'
        mock_p = MagicMock()
        mock_p.mountpoint = 'D:\\'
        mock_p.device = 'D:'
        mock_partitions.return_value = [mock_p]
        mock_label.return_value = 'Crucial MX500'
        
        path = ssd_chrome_automator.find_target_ssd(['Crucial MX500'])
        self.assertEqual(path, 'D:\\')
        mock_label.assert_called_once_with('D:')

    @patch('psutil.disk_usage')
    def test_check_space_success(self, mock_usage):
        mock_u = MagicMock()
        mock_u.free = 600 * (1024**3) # 600 GB
        mock_usage.return_value = mock_u
        
        self.assertTrue(ssd_chrome_automator.check_space('/fake/path', 500))

    @patch('psutil.disk_usage')
    def test_check_space_failure(self, mock_usage):
        mock_u = MagicMock()
        mock_u.free = 100 * (1024**3) # 100 GB
        mock_usage.return_value = mock_u
        
        self.assertFalse(ssd_chrome_automator.check_space('/fake/path', 500))

    @patch('ssd_chrome_automator.check_space')
    def test_redirect_downloads_insufficient_space(self, mock_check_space):
        mock_check_space.return_value = False
        with patch('sys.exit') as mock_exit:
            # We must set side_effect to avoid actually exiting if it's called
            mock_exit.side_effect = Exception("SystemExit")
            try:
                ssd_chrome_automator.redirect_downloads('/ssd', 500)
            except Exception:
                pass
            mock_exit.assert_called_with(1)

    @patch('platform.system')
    def test_get_chrome_downloads_path(self, mock_system):
        mock_system.return_value = 'Linux'
        path = ssd_chrome_automator.get_chrome_downloads_path()
        self.assertTrue(path.endswith('Downloads'))

    @patch('psutil.disk_partitions')
    @patch('platform.system')
    def test_find_target_ssd_found_macos(self, mock_system, mock_partitions):
        mock_system.return_value = 'Darwin'
        mock_p = MagicMock()
        mock_p.mountpoint = '/Volumes/Samsung SSD'
        mock_p.device = '/dev/disk2s1'
        mock_partitions.return_value = [mock_p]

        path = ssd_chrome_automator.find_target_ssd(['Samsung'])
        self.assertEqual(path, '/Volumes/Samsung SSD')

    @patch('ssd_chrome_automator.list_drives')
    @patch('argparse.ArgumentParser.parse_args')
    def test_main_list_flag(self, mock_parse_args, mock_list_drives):
        mock_args = MagicMock()
        mock_args.list = True
        mock_args.restore = False
        mock_parse_args.return_value = mock_args

        ssd_chrome_automator.main()
        mock_list_drives.assert_called_once()

    @patch('builtins.print')
    @patch('psutil.process_iter')
    def test_check_chrome_running(self, mock_process_iter, mock_print):
        mock_proc = MagicMock()
        mock_proc.info = {'name': 'Google Chrome'}
        mock_process_iter.return_value = [mock_proc]

        ssd_chrome_automator.check_chrome_running()
        mock_print.assert_any_call("WARNING: Google Chrome appears to be running.")

if __name__ == '__main__':
    unittest.main()
