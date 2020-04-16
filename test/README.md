# Running the Unit Tests

Note that currently we don't really have comprehensive unit tests for `rwlock`;
we just have a few simple tests that trace the execution of several competing
threads when `SHLock` is used in both modes.

Also note that `SHLock.acquire()` does _not_ work like other lock classes in `threading`
when the `blocking` parameter is set to `False`; in fact, it is rather useless
to set the `blocking` parameter to false, since it is not possible to determine
whether the lock was acquired or not in that case.

To Run the Tests
================
```
# cd to this dir
$ python run_unit_tests.py
```
