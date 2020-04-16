# Copyright (C) 2020 Ankan Pramanick - All rights reserved.
import unittest
import threading
import time
from rwlock import SHLock

_TYPE_READER = 0
_TYPE_WRITER = 1


class _TestThread(threading.Thread):
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
            if _TYPE_READER == self.type:
                try:
                    _TestThread._SHARED_RESOURCE_LOCK.acquire(shared=True)
                    print("[{}] Resource value: [{}]".format(self.name,
                                                             _TestThread._SHARED_RESOURCE))
                except Exception as e:
                    self.counter = 0
                    print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
                finally:
                    _TestThread._SHARED_RESOURCE_LOCK.release()
            else:  # Writer
                try:
                    _TestThread._SHARED_RESOURCE_LOCK.acquire(shared=False)
                    print("[{}] Updating resource with '{}' ...".format(self.name, append_char))
                    _TestThread._SHARED_RESOURCE = _TestThread._SHARED_RESOURCE + append_char
                except Exception as e:
                    self.counter = 0
                    print("[{}] [error] Aborting because of exception: {}".format(self.name, e))
                finally:
                    _TestThread._SHARED_RESOURCE_LOCK.release()
        print("Exiting {}".format(self.name))


class RWLockTest(unittest.TestCase):
    """Unit tests for the rwlock module.

    Note that currently we don't really have comprehensive unit tests for SHLock; we just have
    a simple single test that traces the execution of several competing threads.
    """

    def test_simple(self):

        r1 = _TestThread(_TYPE_READER, 1, "Reader 1", 25, 0.1)
        r2 = _TestThread(_TYPE_READER, 2, "Reader 2", 15, 0.15)
        r3 = _TestThread(_TYPE_READER, 3, "Reader 3", 4, 0.5)
        w1 = _TestThread(_TYPE_WRITER, 4, "Writer 1", 5, 0.05)
        w2 = _TestThread(_TYPE_WRITER, 5, "Writer 2", 7, 0.3)

        all_threads = [r1, r2, r3, w1, w2]
        for t in all_threads:
            t.start()
        for t in all_threads:
            t.join(timeout=4)
            self.assertFalse(t.is_alive())
