import unittest
from unittest.mock import patch, MagicMock
import os
import watchdog_mover

class TestWatchdogMover(unittest.TestCase):

    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('shutil.move')
    @patch('os.makedirs')
    @patch('ssd_chrome_automator.find_target_ssd')
    def test_process_file_large_iso(self, mock_find_ssd, mock_makedirs, mock_move, mock_exists, mock_getsize):
        # Setup
        mock_find_ssd.return_value = '/Volumes/Test'
        mock_exists.side_effect = lambda x: True if x == 'test.iso' else False
        mock_getsize.return_value = 600 * 1024 * 1024 # 600 MB

        handler = watchdog_mover.DownloadHandler(['Test'])
        handler.process_file('test.iso')

        # Verify
        mock_move.assert_called_once()
        args, _ = mock_move.call_args
        self.assertEqual(args[0], 'test.iso')
        self.assertTrue(args[1].startswith('/Volumes/Test/SSD_Downloads/test.iso'))

    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('shutil.move')
    def test_process_file_small_non_target(self, mock_move, mock_exists, mock_getsize):
        # Setup
        mock_exists.return_value = True
        mock_getsize.return_value = 10 * 1024 * 1024 # 10 MB

        handler = watchdog_mover.DownloadHandler(['Test'])
        handler.process_file('test.txt')

        # Verify
        mock_move.assert_not_called()

    @patch('os.path.getsize')
    @patch('os.path.exists')
    @patch('shutil.move')
    @patch('os.makedirs')
    @patch('ssd_chrome_automator.find_target_ssd')
    def test_process_file_small_target_extension(self, mock_find_ssd, mock_makedirs, mock_move, mock_exists, mock_getsize):
        # Setup
        mock_find_ssd.return_value = '/Volumes/Test'
        mock_exists.side_effect = lambda x: True if x == 'test.nds' else False
        mock_getsize.return_value = 10 * 1024 * 1024 # 10 MB (Small but .nds)

        handler = watchdog_mover.DownloadHandler(['Test'])
        handler.process_file('test.nds')

        # Verify
        mock_move.assert_called_once()

    def test_skip_temp_files(self):
        with patch('os.path.getsize') as mock_getsize:
            handler = watchdog_mover.DownloadHandler(['Test'])
            handler.process_file('test.crdownload')
            mock_getsize.assert_not_called()

if __name__ == '__main__':
    unittest.main()
