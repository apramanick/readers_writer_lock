from distutils.core import setup

import rwlock

VERSION = rwlock.__version__

NAME = "rwlock"
DESCRIPTION = "A Python implementation of a readers/writer lock"
LONG_DESC = rwlock.__doc__
AUTHOR = "Ryan Kelly"
AUTHOR_EMAIL = "ryan@rfk.id.au"
URL = "https://github.com/apramanick/readers_writer_lock"
LICENSE = "MIT"
KEYWORDS = "thread threading lock mutex read-write"

setup(name=NAME,
      python_requires='>=3.8',
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      long_description=LONG_DESC,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=["rwlock"]
      )
