# readers_writer_lock

A clone of the `SHLock` class (and associated helper classes) from the last published version
(version 0.3.1) of Python `threading2` from PyPi, written by __Ryan Kelly__ (see
[the original project](https://github.com/rfk/threading2)).  I created this clone
since we needed to continue using the `SHLock` class in Python 3.x, and the original had stopped
being maintained (it is archived), and was stuck at Python 2.x.

This project keeps only the `SHLock` class (and its essential helper classes and components)
from the original `threading2` package.  The only modifications I have made is to port this code
to Python 3.8.

Support Considerations
======================
Currently, I have no plans to support this long-term, since this is a temporary measure to
port our own code to Python 3.x as painlessly as possible; in future, we might move to using
a different readers-writers lock implementation in Python, at which time I will drop support
for this.

