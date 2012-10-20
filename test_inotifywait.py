import os
import subprocess
import tempfile
import time
import unittest


class TestInotifywait(unittest.TestCase):
    _INOTIFYWAIT_DEFAULT_LOCATION = '/usr/local/bin/inotifywait'

    @classmethod
    def _inotifywait_file_exists(cls):
        inotifywait = os.path.abspath(cls._INOTIFYWAIT_DEFAULT_LOCATION)
        return os.path.exists(inotifywait)

    @classmethod
    def _inotifywait_is_executable(cls):
        inotifywait = os.path.abspath(cls._INOTIFYWAIT_DEFAULT_LOCATION)
        return os.access(inotifywait, os.X_OK)

    @classmethod
    def _ensure_inotifywait_installed(cls):
        installed = (cls._inotifywait_file_exists() and
                cls._inotifywait_is_executable())
        if not installed:
            raise ValueError("inotifywait was not found at the expected location"
                    " ({0}) or is not an executable file".format(
                        cls._INOTIFYWAIT_DEFAULT_LOCATION))

    @classmethod
    def setUpClass(cls):
        cls._ensure_inotifywait_installed()

    def _make_temp_file(self):
        handle, path = tempfile.mkstemp()
        os.fdopen(handle).close()
        return path

    def setUp(self):
        self._inotify = self._INOTIFYWAIT_DEFAULT_LOCATION
        self._testfile = self._make_temp_file()

    def tearDown(self):
        if hasattr(self, '_testfile'):
            print 'Removing {0}'.format(self._testfile)
            os.remove(self._testfile)

    def test_detects_close_write(self):
        cmd = [self._inotify,
               "--quiet",
               "--event", "CLOSE_WRITE",
               "--format", "'%e'",
               "--timeout", "5",
               self._testfile]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        def _write_to_file():
            # the write might happen before inotifywait notices it
            time.sleep(0.001)
            fd = open(self._testfile, 'w')
            fd.write(' '.join(cmd))
            fd.close()

        _write_to_file()
        stdout, _ = proc.communicate()

        self.assertEqual(0, proc.returncode)
        self.assertIn("CLOSE_WRITE", stdout)
