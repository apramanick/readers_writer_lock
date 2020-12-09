"""

rwlock: A Python implementation of a readers/writer lock.

This is a drop-in replacement for the threading2.SHLock class, using the implementation
from that library.  The threading2 library (https://github.com/rfk/threading2) is no longer
maintained (its github repository has been archived), and is stuck at Python 2.x.  This
implementation has been ported to work with Python 3.8.

Note that the SHLock class is an implementation of the classic readers-writer lock (see,
for example, https://en.wikipedia.org/wiki/Readers%E2%80%93writer_lock).  A read/write lock
allows concurrent access for read-only operations, while write operations require exclusive
access.  This means that multiple threads can read the data in parallel, but an exclusive
lock is needed for writing or modifying data. When a writer is writing the data, all other
writers or readers will be blocked until the writer is finished writing.

The following API niceties are also included:

    * all blocking methods take a "timeout" argument and return a success code
    * all exposed objects are actual classes and can be safely subclassed

"""
import sys
_MIN_PYTHON = (3, 8)
if sys.version_info < _MIN_PYTHON:
    sys.exit("Python {}.{} or later is required.".format(_MIN_PYTHON[0], _MIN_PYTHON[1]))

__ver_major__ = 0
__ver_minor__ = 5
__ver_patch__ = 1
__ver_sub__ = ""
__version__ = "{0}.{1}.{2}{3}".format(__ver_major__, __ver_minor__, __ver_patch__, __ver_sub__)

from rwlock.rw_lock import *

__all__ = ["Condition", "Lock", "RLock", "SHLock"]
