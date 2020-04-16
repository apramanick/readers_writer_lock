
from threading import *
# noinspection PyUnresolvedReferences,PyProtectedMember
from threading import _Condition, _RLock, _allocate_lock, _get_ident
from time import sleep as _sleep
from time import time as _time

__all__ = ["Condition", "Lock", "RLock", "SHLock"]


# noinspection PyUnresolvedReferences
class _ContextManagerMixin(object):
    """Simple mixin mapping __enter__/__exit__ to acquire/release."""

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()


class Lock(_ContextManagerMixin):
    """Class-based Lock object.

    This is a very thin wrapper around Python's native lock objects.  It's
    here to provide ease of subclassing and to add a "timeout" argument
    to Lock.acquire().
    """

    def __init__(self):
        self.__lock = _allocate_lock()
        super(Lock, self).__init__()

    def acquire(self, blocking=True, timeout=None):
        """Attempt to acquire this lock.

        If the optional argument "blocking" is True and "timeout" is None,
        this methods blocks until is successfully acquires the lock.  If
        "blocking" is False, it returns immediately if the lock could not
        be acquired.  Otherwise, it blocks for at most "timeout" seconds
        trying to acquire the lock.

        In all cases, this methods returns True if the lock was successfully
        acquired and False otherwise.
        """
        if timeout is None:
            return self.__lock.acquire(blocking)
        else:
            # Simulated timeout using progressively longer sleeps.
            # This is the same timeout scheme used in the stdlib Condition
            # class.  If there's lots of contention on the lock then there's
            # a good chance you won't get it; but then again, Python doesn't
            # guarantee fairness anyway.
            end_time = _time() + timeout
            delay = 0.0005
            while not self.__lock.acquire(False):
                remaining = end_time - _time()
                if remaining <= 0:
                    return False
                delay = min(delay * 2, remaining, 0.05)
                _sleep(delay)
            return True

    def release(self):
        """Release this lock."""
        self.__lock.release()


class RLock(_ContextManagerMixin, _RLock):
    """Re-implemented RLock object.

    This is pretty much a direct clone of the RLock object from the standard
    threading module; the only difference is that it uses a custom Lock class
    so that acquire() has a "timeout" parameter.
    """

    _LockClass = Lock

    def __init__(self):
        super(RLock, self).__init__()
        self.__block = self._LockClass()
        self.__owner = None
        self.__count = 0

    def acquire(self, blocking=True, timeout=None):
        me = _get_ident()
        if self.__owner == me:
            self.__count += 1
            return True
        if self.__block.acquire(blocking, timeout):
            self.__owner = me
            self.__count = 1
            return True
        return False

    def release(self):
        if self.__owner != _get_ident():
            raise RuntimeError("cannot release un-acquired lock")
        self.__count -= 1
        if not self.__count:
            self.__owner = None
            self.__block.release()

    def _is_owned(self):
        return self.__owner == _get_ident()


class Condition(_Condition):
    """Re-implemented Condition class.

    This is pretty much a direct clone of the Condition class from the standard
    threading module; the only difference is that it uses a custom Lock class
    so that acquire() has a "timeout" parameter.
    """

    _LockClass = RLock
    _WaiterLockClass = Lock

    def __init__(self, lock=None):
        if lock is None:
            lock = self._LockClass()
        super(Condition, self).__init__(lock)

    # This is essentially the same as the base version, but it returns
    # True if the wait was successful and False if it timed out.
    def wait(self, timeout=None):
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-acquired lock")
        waiter = self._WaiterLockClass()
        waiter.acquire()
        self.__waiters.append(waiter)
        saved_state = self._release_save()
        try:
            if not waiter.acquire(timeout=timeout):
                try:
                    self.__waiters.remove(waiter)
                except ValueError:
                    pass
                return False
            else:
                return True
        finally:
            self._acquire_restore(saved_state)


class SHLock(_ContextManagerMixin):
    """Shareable lock class.

    This functions just like an RLock except that you can also request a
    "shared" lock mode.  Shared locks can co-exist with other shared locks
    but block exclusive locks.  You might also know this as a read/write lock.

    Currently attempting to upgrade or downgrade between shared and exclusive
    locks will cause a deadlock.  This restriction may go away in future.
    """

    class Context(_ContextManagerMixin):

        def __init__(self, parent,
                     blocking=True, timeout=None, shared=False):
            self.parent = parent
            self.blocking = blocking
            self.timeout = timeout
            self.shared = shared

        def acquire(self):
            self.parent.acquire(blocking=self.blocking,
                                timeout=self.timeout,
                                shared=self.shared)

        def release(self):
            self.parent.release()

    _LockClass = Lock
    _ConditionClass = Condition

    def __init__(self):
        self._lock = self._LockClass()
        # When a shared lock is held, is_shared will give the cumulative
        # number of locks and _shared_owners maps each owning thread to
        # the number of locks is holds.
        self.is_shared = 0
        self._shared_owners = {}
        # When an exclusive lock is held, is_exclusive will give the number
        # of locks held and _exclusive_owner will give the owning thread
        self.is_exclusive = 0
        self._exclusive_owner = None
        # When someone is forced to wait for a lock, they add themselves
        # to one of these queues along with a "waiter" condition that
        # is used to wake them up.
        self._shared_queue = []
        self._exclusive_queue = []
        # This is for recycling waiter objects.
        self._free_waiters = []

    def __call__(self, blocking=True, timeout=None, shared=False):
        return SHLock.Context(self, blocking=blocking,
                              timeout=timeout, shared=shared)

    def acquire(self, blocking=True, timeout=None, shared=False):
        """Acquire the lock in shared or exclusive mode."""
        with self._lock:
            if shared:
                self._acquire_shared(blocking, timeout)
            else:
                self._acquire_exclusive(blocking, timeout)
            assert not (self.is_shared and self.is_exclusive)

    def release(self):
        """Release the lock."""
        # This decrements the appropriate lock counters, and if the lock
        # becomes free, it looks for a queued thread to hand it off to.
        # By doing the hand-off here we ensure fairness.
        me = currentThread()
        with self._lock:
            if self.is_exclusive:
                if self._exclusive_owner is not me:
                    raise RuntimeError("release() called on un-acquired lock")
                self.is_exclusive -= 1
                if not self.is_exclusive:
                    self._exclusive_owner = None
                    # If there are waiting shared locks, issue it to them
                    # all and then wake everyone up.
                    if self._shared_queue:
                        for (thread, waiter) in self._shared_queue:
                            self.is_shared += 1
                            self._shared_owners[thread] = 1
                            waiter.notify()
                        del self._shared_queue[:]
                    # Otherwise, if there are waiting exclusive locks,
                    # they get first dibs on the lock.
                    elif self._exclusive_queue:
                        (thread, waiter) = self._exclusive_queue.pop(0)
                        self._exclusive_owner = thread
                        self.is_exclusive += 1
                        waiter.notify()
            elif self.is_shared:
                try:
                    self._shared_owners[me] -= 1
                    if self._shared_owners[me] == 0:
                        del self._shared_owners[me]
                except KeyError:
                    raise RuntimeError("release() called on un-acquired lock")
                self.is_shared -= 1
                if not self.is_shared:
                    # If there are waiting exclusive locks, they get first dibs on the lock.
                    if self._exclusive_queue:
                        (thread, waiter) = self._exclusive_queue.pop(0)
                        self._exclusive_owner = thread
                        self.is_exclusive += 1
                        waiter.notify()
                    else:
                        assert not self._shared_queue
            else:
                raise RuntimeError("release() called on un-acquired lock")

    def _acquire_shared(self, blocking=True, timeout=None):
        me = currentThread()
        # Each case: acquiring a lock we already hold.
        if self.is_shared and me in self._shared_owners:
            self.is_shared += 1
            self._shared_owners[me] += 1
            return True
        # If the lock is already spoken for by an exclusive, add us
        # to the shared queue and it will give us the lock eventually.
        if self.is_exclusive or self._exclusive_queue:
            if self._exclusive_owner is me:
                raise RuntimeError("can't downgrade SHLock object")
            if not blocking:
                return False
            waiter = self._take_waiter()
            try:
                self._shared_queue.append((me, waiter))
                if not waiter.wait(timeout=timeout):
                    self._shared_queue.remove((me, waiter))
                    return False
                assert not self.is_exclusive
            finally:
                self._return_waiter(waiter)
        else:
            self.is_shared += 1
            self._shared_owners[me] = 1

    def _acquire_exclusive(self, blocking=True, timeout=None):
        me = currentThread()
        # Each case: acquiring a lock we already hold.
        if self._exclusive_owner is me:
            assert self.is_exclusive
            self.is_exclusive += 1
            return True
        # If the lock is already spoken for, add us to the exclusive queue.
        # This will eventually give us the lock when it's our turn.
        if self.is_shared or self.is_exclusive:
            if not blocking:
                return False
            waiter = self._take_waiter()
            try:
                self._exclusive_queue.append((me, waiter))
                if not waiter.wait(timeout=timeout):
                    self._exclusive_queue.remove((me, waiter))
                    return False
            finally:
                self._return_waiter(waiter)
        else:
            self._exclusive_owner = me
            self.is_exclusive += 1

    def _take_waiter(self):
        try:
            return self._free_waiters.pop()
        except IndexError:
            return self._ConditionClass(self._lock)

    def _return_waiter(self, waiter):
        self._free_waiters.append(waiter)
