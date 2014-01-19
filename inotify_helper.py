import os
import subprocess
import unittest
import tempfile
import time


class TestInotify(unittest.TestCase):
    """Base class for testing inotifywait and inotifywatch"""

    # Subclasses should override this.
    _INOTIFY_BINARY_LOCATION = ''

    @classmethod
    def _inotify_file_exists(cls):
        inotifywait = os.path.abspath(cls._INOTIFY_BINARY_LOCATION)
        return os.path.exists(inotifywait)

    @classmethod
    def _inotify_is_executable(cls):
        inotifywait = os.path.abspath(cls._INOTIFY_BINARY_LOCATION)
        return os.access(inotifywait, os.X_OK)

    @classmethod
    def _ensure_inotify_installed(cls):
        installed = (cls._inotify_file_exists() and
                cls._inotify_is_executable())
        if not installed:
            raise ValueError("{0} was not found at the expected location"
                    " ({1}) or is not an executable file".format(
                        os.path.basename(cls._INOTIFY_BINARY_LOCATION),
                        cls._INOTIFY_BINARY_LOCATION))

    @classmethod
    def setUpClass(cls):
        cls._ensure_inotify_installed()

    def _make_temp_file(self, prefix=None, suffix=None):
        kwargs = {}
        if prefix is not None:
            kwargs['prefix'] = prefix
        if suffix is not None:
            kwargs['suffix'] = suffix
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
        self._inotify = self._INOTIFY_BINARY_LOCATION
        self._testfile = self._make_temp_file()

    def tearDown(self):
        if hasattr(self, '_testfile'):
            print('Removing {0}'.format(self._testfile))
            if os.path.exists(self._testfile):
                os.remove(self._testfile)

