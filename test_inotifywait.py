import os
import shutil
import subprocess

from inotify_helper import TestInotify


class TestInotifywait(TestInotify):
    _INOTIFY_BINARY_LOCATION = '/usr/local/bin/inotifywait'

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

    def test_exclude_and_excludei_mutually_exclusiv(self):
        cmd = [self._inotify,
               "--exclude", "exclude.*?",
               "--excludei", "EXCLUDEI.*?",
               self._testfile]

        proc = self._get_process(cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, with_sleep=False)
        stdout, stderr = proc.communicate()

        expected = '--exclude and --excludei cannot both be specified.'
        self.assertFalse(len(stdout) > 0)
        self.assertEqual(expected, stderr.strip())

    def test_exclude_specified_twice(self):
        """Only the last --exclude is taken into consideration. You
        cannot specify multiple --exclude options, under the assumption that
        they'll be AND-ed.
        """
        sut = self._make_temp_file(prefix='excluded')
        cmd = [self._inotify,
               "--quiet",
               "--exclude", "tmp.*?",  # this is not actually excluded, because of the next line
               "--exclude", "excluded.*?",  # this is the only one excluded
               "--timeout", "2",
               "--event", "OPEN",
               self._testfile, sut]

        proc = self._get_process(cmd, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        # Generate an open event
        open(sut)
        open(self._testfile)

        stdout, stderr = proc.communicate()
        os.remove(sut)

        self.assertEqual(0, proc.returncode)

        # Only events for self._testfile are recorded
        expected = "{0} OPEN".format(self._testfile)
        self.assertEqual(expected, stdout.strip())

        # A warning is sent on stderr about --exclude being specified twice
        expected = "--exclude: only the last option will be taken into consideration."
        self.assertEqual(expected, stderr.strip())

    def test_timeout_handles_large_values(self):
        """Whenever a timeout value larger that ULLONG_MAX is provided,
        inotifywait displays an error message and returns.
        """
        timeout = u"999999999999999999999999999999999999999999"
        sut = self._make_temp_file(prefix='timeout')
        cmd = [self._inotify,
               "--quiet",
               "--timeout", timeout,
               self._testfile, sut]

        proc = self._get_process(cmd, stderr=subprocess.PIPE)

        _, stderr = proc.communicate()
        os.remove(sut)

        expected = ("The timeout value you provided is not in the "
                "representable range.")
        self.assertEqual(expected, stderr.strip())

    def test_timeout_handles_invalid_values(self):
        sut = self._make_temp_file(prefix='timeout')
        cmd = [self._inotify,
               "--quiet",
               "--timeout", "abc",
               self._testfile, sut]

        proc = self._get_process(cmd, stderr=subprocess.PIPE)

        _, stderr = proc.communicate()
        os.remove(sut)

        expected = ("'abc' is not a valid timeout value.\n"
                "Please specify an integer of value 0 or greater.")
        self.assertEqual(expected, stderr.strip())

