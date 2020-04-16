# Running the unit tests

Note that currently we don't really have comprehensive unit tests for `rwlock`;
we just have a single, simple test that traces the execution of several competing
threads when `SHLock` is used in both modes.

To run the tests:
```
# cd to this dir
$ python run_unit_tests.py
```
