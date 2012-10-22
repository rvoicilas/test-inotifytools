import os
import subprocess

from inotify_helper import TestInotify


class TestInotifywatch(TestInotify):
    _INOTIFY_BINARY_LOCATION = '/usr/local/bin/inotifywatch'

    def test_exclude_specified_twice(self):
        """Only the last --exclude is taken into consideration. You
        cannot specify multiple --exclude options, under the assumption that
        they'll be AND-ed.
        """
        sut = self._make_temp_file(prefix='excluded')
        cmd = [self._inotify,
               "--exclude", "tmp.*?",  # this is not actually excluded, because of the next line
               "--exclude", "excluded.*?",  # this is the only one excluded
               "--timeout", "1",
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

        # Boilerplate to extract the total number of events,
        # the number of OPEN events and the filename on which these
        # events happened.
        stats = stdout.strip().split('\n')[1]
        stats = [s for s in stats.split(' ') if len(s)]
        total_events, event_open, events_file = stats

        self.assertEqual(1, int(total_events))
        self.assertEqual(1, int(event_open))
        self.assertEqual(self._testfile, events_file)
