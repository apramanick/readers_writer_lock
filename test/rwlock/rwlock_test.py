# Copyright (C) 2020 Ankan Pramanick - All rights reserved.
import threading
import time
import unittest
import sys
import io
import re
import random

from rwlock import SHLock

_TYPE_READER = 0
_TYPE_WRITER = 1
_WRITER_OUTPUT_PATTERN = re.compile(r"^\[Writer")


class _TestThread1(threading.Thread):
    """A thread class to use in our unit tests."""

    _SHARED_RESOURCE = "0"
    _SHARED_RESOURCE_LOCK = SHLock()

    def __init__(self, thread_type, thread_id, name, total_step_count, step_delay):
        """Ctor.

        @param int thread_type:      Thread type, one of _TYPE_READER or _TYPE_WRITER.
        @param int thread_id:        Thread ID.
        @param str name:             Thread name.
        @param int total_step_count: Number of times the run() method should do some work.
        @param float step_delay:     The delay in seconds between the work steps in the run()
                                     method.
        """
        threading.Thread.__init__(self, name=name)
        self.type = thread_type
        self.id = thread_id
        self.name = name
        self.counter = total_step_count
        self.step_delay = step_delay

    def run(self):
        append_char = None
        if _TYPE_WRITER == self.type:
            append_char = "{}".format(self.id)
        print("Starting {}".format(self.name))
        while self.counter > 0:
            time.sleep(self.step_delay)
            self.counter -= 1
            got_lock = False
            if _TYPE_READER == self.type:
                try:
                    _TestThread1._SHARED_RESOURCE_LOCK.acquire(shared=True)
                    got_lock = True
                    print("[{}] Resource value: [{}]".format(self.name,
                                                             _TestThread1._SHARED_RESOURCE))
                except Exception as e:
                    self.counter = 0
                    print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
                finally:
                    if got_lock:
                        _TestThread1._SHARED_RESOURCE_LOCK.release()
            else:  # Writer
                try:
                    _TestThread1._SHARED_RESOURCE_LOCK.acquire(shared=False)
                    got_lock = True
                    print("[{}] Updating resource with '{}' ...".format(self.name, append_char))
                    _TestThread1._SHARED_RESOURCE = _TestThread1._SHARED_RESOURCE + append_char
                except Exception as e:
                    self.counter = 0
                    print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
                finally:
                    if got_lock:
                        _TestThread1._SHARED_RESOURCE_LOCK.release()
        print("Exiting {}".format(self.name))


class _TestThread2(threading.Thread):
    """A thread class to use in our unit tests."""

    _SHARED_RESOURCE_LOCK = SHLock()
    _WRITER_SLEEP_TIME = 0.5  # seconds

    def __init__(self, thread_type, thread_id, name, outfile=sys.stdout):
        """Ctor.

        @param int thread_type: Thread type, one of _TYPE_READER or _TYPE_WRITER.
        @param int thread_id:   Thread ID.
        @param str name:        Thread name.
        @param stream outfile:  Object to stream output to.
        """
        threading.Thread.__init__(self, name=name)
        self.type = thread_type
        self.id = thread_id
        self.name = name
        self.outfile = outfile

    def run(self):
        # print("{} starting".format(self.name))
        got_lock = False
        if _TYPE_READER == self.type:
            try:
                _TestThread2._SHARED_RESOURCE_LOCK.acquire(shared=True)
                got_lock = True
                print("[{}] Acquired lock".format(self.name), file=self.outfile)
                # Pause enough for other readers a chance to get the shared lock while we are
                # still holding on to it:
                delay = (random.randint(1, 4)) / 100.0
                time.sleep(delay)
            except Exception as e:
                print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
            finally:
                if got_lock:
                    _TestThread2._SHARED_RESOURCE_LOCK.release()
                    print("[{}] Released lock".format(self.name), file=self.outfile)
        else:  # Writer
            try:
                _TestThread2._SHARED_RESOURCE_LOCK.acquire(shared=False)
                got_lock = True
                print("[{}] Acquired lock".format(self.name), file=self.outfile)
                time.sleep(_TestThread2._WRITER_SLEEP_TIME)
            except Exception as e:
                print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
            finally:
                if got_lock:
                    _TestThread2._SHARED_RESOURCE_LOCK.release()
                    print("[{}] Released lock".format(self.name), file=self.outfile)
        # print("{} exiting".format(self.name))


class RWLockTest(unittest.TestCase):
    """Unit tests for the rwlock module.

    Note that currently we don't really have comprehensive unit tests for rwlock;
    we just have a few simple tests that trace the execution of several competing
    threads when SHLock is used in both modes.
    """

    def test_simple(self):
        r1 = _TestThread1(_TYPE_READER, 1, "Reader 1", 25, 0.1)
        r2 = _TestThread1(_TYPE_READER, 2, "Reader 2", 15, 0.15)
        r3 = _TestThread1(_TYPE_READER, 3, "Reader 3", 4, 0.5)
        w1 = _TestThread1(_TYPE_WRITER, 4, "Writer 1", 5, 0.05)
        w2 = _TestThread1(_TYPE_WRITER, 5, "Writer 2", 7, 0.3)
        all_threads = [r1, r2, r3, w1, w2]
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join(timeout=5)
            self.assertFalse(t.is_alive())

    def test_exclusive_lockout_writer_first(self):
        with io.StringIO() as output:
            w0 = _TestThread2(_TYPE_WRITER, 0, "Writer 0", output)
            r1 = _TestThread2(_TYPE_READER, 1, "Reader 1", output)
            r2 = _TestThread2(_TYPE_READER, 2, "Reader 2", output)
            r3 = _TestThread2(_TYPE_READER, 3, "Reader 3", output)
            r4 = _TestThread2(_TYPE_READER, 4, "Reader 4", output)
            r5 = _TestThread2(_TYPE_READER, 5, "Reader 5", output)
            all_threads = [w0, r1, r2, r3, r4, r5]
            w0.start()  # Start the writer first: it should be able to grab the lock exclusively
            time.sleep(0.01)
            # None of reader threads should be able to acquire the lock until after
            # the writer releases it:
            for t in all_threads:
                if t is not w0:
                    t.start()
            for t in all_threads:
                t.join(timeout=2)
                self.assertFalse(t.is_alive())
            # The first two lines in the captured output should always be from the writer:
            lines = output.getvalue().splitlines()
            self.assertEqual(12, len(lines))
            line0 = lines[0].strip()
            line1 = lines[1].strip()
            self.assertEqual("[Writer 0] Acquired lock", line0)
            self.assertEqual("[Writer 0] Released lock", line1)

    def test_exclusive_lockout_writer_later(self):
        with io.StringIO() as output:
            w0 = _TestThread2(_TYPE_WRITER, 0, "Writer 0", output)
            r1 = _TestThread2(_TYPE_READER, 1, "Reader 1", output)
            r2 = _TestThread2(_TYPE_READER, 2, "Reader 2", output)
            r3 = _TestThread2(_TYPE_READER, 3, "Reader 3", output)
            r4 = _TestThread2(_TYPE_READER, 4, "Reader 4", output)
            r5 = _TestThread2(_TYPE_READER, 5, "Reader 5", output)
            all_threads = [r1, r2, w0, r3, r4, r5]
            for t in all_threads:
                time.sleep(0.001)
                t.start()
            for t in all_threads:
                t.join(timeout=2)
                self.assertFalse(t.is_alive())
            lines = output.getvalue().splitlines()
            self.assertEqual(12, len(lines))
            # There should be no "[Reader ..." lines in between the two "[Writer ..." lines:
            for i in range(len(lines)):
                line = lines[i].strip()
                if _WRITER_OUTPUT_PATTERN.search(line):
                    self.assertLess(i, len(lines) - 1)
                    next_line = lines[i + 1]
                    self.assertIsNotNone(_WRITER_OUTPUT_PATTERN.search(next_line))
                    break
