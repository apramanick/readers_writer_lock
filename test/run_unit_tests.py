# Copyright (C) 2020 Ankan Pramanick - All rights reserved.
"""
Runs the unit tests.

Note that this MUST be invoked from the directory in which this script is located.
"""
import argparse
import collections
import os
import sys
import unittest


_VERBOSITY_LOWER_LIMIT = 0
_VERBOSITY_UPPER_LIMIT = 3
_TOP_LEVEL_TEST_MODULE = "rwlock"

CmdLineArgs = collections.namedtuple("CmdLineArgs",
                                     ["verbosity"])  # int


def _add_code_root():
    """
    Adds the root of the code tree (that is being tested) to the head of sys.path.

    Note that it is important to add the *code* tree root ahead of the *test* tree root
    (which will be added automatically since this script is intended to be invoked from
    the test tree root), because we might have a hierarchy within the test tree that looks
    identical, in terms of package/module names, to the code tree.  Hence, in order for
    imports within the test code to be able to load the proper code that is being tested
    (and not try to find corresponding names/modules/classes/etc. from the *test* tree,
    which are obviously not there), the path to the code tree must be ahead in the search path.
    """
    parent_dir_of_this_script = os.path.dirname(os.path.realpath(__file__))
    path_to_main_code_root = os.path.realpath(os.path.join(parent_dir_of_this_script, ".."))
    sys.path.insert(0, path_to_main_code_root)


def _parse_command_line():
    """
    Parses the command line for this script.

    @return CmdLineArgs: An object encapsulating the values for the command line args.
    """
    # Customizing the help formatter used with a max_help_position larger than the current
    # default of 24 gives a little more room in the help printout, between the parameter/value
    # list and the help string:
    def formatter(prog): return argparse.ArgumentDefaultsHelpFormatter(prog,
                                                                       max_help_position=36)

    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(
        formatter_class=formatter,  # The above-defined formatter
        description="Runs unit tests for rwlock.")
    parser.add_argument("-v", "--verbosity",
                        metavar="VAL",
                        type=int,
                        default="2",
                        help="the value for test output verbosity; must be a non-negative "
                             "integer in between {0} and {1}".format(_VERBOSITY_LOWER_LIMIT,
                                                                     _VERBOSITY_UPPER_LIMIT))
    args = parser.parse_args()
    return CmdLineArgs(verbosity=args.verbosity)


def _run_tests(verbosity):
    """
    Creates the test-suite through test discovery from the root of the test tree, and runs it.

    NOTE:
        - Test suite dirs must look like python modules, i.e., all file names must be valid
          Python identifiers (e.g., there shouldn't be any hyphens in the file names), and
          the dir must have a __init__.py file.
        - Test class files must end in the suffix "_test.py".
        - Test method names in test classes must start with the prefix "test_".

    @param int verbosity: The verbosity of the test output.
    @return unittest.result.TestResult: The test result.
    """
    loader = unittest.TestLoader()
    tests = loader.discover(_TOP_LEVEL_TEST_MODULE, pattern="*_test.py")
    # noinspection PyTypeChecker
    test_runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=verbosity)
    # noinspection PyUnresolvedReferences
    return test_runner.run(tests)


def main():
    """The main entry point."""
    _add_code_root()
    cmd_line_args = _parse_command_line()
    # The following import only works after _add_code_root():
    print("Running tests for rwlock ...")
    print("[Using {}]".format(sys.executable))
    test_result = _run_tests(cmd_line_args.verbosity)
    if test_result.wasSuccessful():
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
