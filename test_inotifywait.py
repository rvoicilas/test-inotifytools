import os
import shutil
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

    def _make_temp_file(self, prefix=None):
        kwargs = prefix is not None and {'prefix': prefix} or {}
        handle, path = tempfile.mkstemp(**kwargs)
        os.fdopen(handle).close()
        return path

    def _get_process(self, cmd, stdout=None, stderr=None, with_sleep=True):
        """Mostly for hiding the time.sleep() call, which is required
        if the events for the monitored files happen before
        inotifywait is done setting up the watches.
        """
        proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr)
        if with_sleep:
            time.sleep(0.001)
        return proc

    def setUp(self):
        self._inotify = self._INOTIFYWAIT_DEFAULT_LOCATION
        self._testfile = self._make_temp_file()

    def tearDown(self):
        if hasattr(self, '_testfile'):
            print 'Removing {0}'.format(self._testfile)
            if os.path.exists(self._testfile):
                os.remove(self._testfile)

    def test_detects_close_write(self):
        cmd = [self._inotify,
               "--quiet",
               "--event", "CLOSE_WRITE",
               "--format", "'%e'",
               "--timeout", "5",
               self._testfile]

        proc = self._get_process(cmd, stdout=subprocess.PIPE)

        # Generate a close_write event
        with open(self._testfile, 'w') as fd:
            fd.write(' '.join(cmd))

        stdout, _ = proc.communicate()

        self.assertEqual(0, proc.returncode)
        self.assertIn("CLOSE_WRITE", stdout)

    def test_move_self(self):
        cmd = [self._inotify,
               "--quiet",
               "--event", "MOVE_SELF",
               "--format", "'%e'",
               "--timeout", "5",
               self._testfile]

        proc = self._get_process(cmd, stdout=subprocess.PIPE)

        # Generate a move_self event
        dest = self._make_temp_file()
        shutil.move(self._testfile, dest)

        stdout, _ = proc.communicate()
        os.remove(dest)

        self.assertEqual(0, proc.returncode)
        self.assertIn("MOVE_SELF", stdout)

    def test_include(self):
        """Make sure that only events for files specified with
        --include are processed by inotifywait.
        """

        sut = self._make_temp_file(prefix='include')

        cmd = [self._inotify,
               "--quiet",
               "--event", "OPEN",
               "--timeout", "5",
               "--include", "include.*?",
               self._testfile, sut]

        proc = self._get_process(cmd, stdout=subprocess.PIPE)

        # Generate an open event for each file that's monitored
        open(self._testfile)
        open(sut)

        stdout, _ = proc.communicate()
        os.remove(sut)

        self.assertEqual(0, proc.returncode)
        expected = '{0} OPEN'.format(sut)
        self.assertEqual(expected, stdout.strip())


    def test_includei(self):
        """Make sure that only events for files specified with
        --includei are processed by inotifywait.
        """

        sut = self._make_temp_file(prefix='includei')

        cmd = [self._inotify,
               "--quiet",
               "--event", "OPEN",
               "--timeout", "5",
               "--includei", "INCLUDEI.*?",
               self._testfile, sut]

        proc = self._get_process(cmd, stdout=subprocess.PIPE)

        # Generate an open event for each file that's monitored
        open(self._testfile)
        open(sut)

        stdout, _ = proc.communicate()
        os.remove(sut)

        self.assertEqual(0, proc.returncode)
        expected = '{0} OPEN'.format(sut)
        self.assertEqual(expected, stdout.strip())


    def test_include_and_includei_mutually_exclusive(self):
        cmd = [self._inotify,
               "--include", "include.*?",
               "--includei", "INCLUDEI.*?",
               self._testfile]

        proc = self._get_process(cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, with_sleep=False)
        stdout, stderr = proc.communicate()

        expected = '--include and --includei cannot both be specified.'
        self.assertFalse(len(stdout) > 0)
        self.assertEqual(expected, stderr.strip())
