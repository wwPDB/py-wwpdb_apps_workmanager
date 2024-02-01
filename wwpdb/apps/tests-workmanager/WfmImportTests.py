##
# File: WfmImportTests.py
# Date:  05-Nov-2018  E. Peisach
#
# Updates:
##
"""Test cases for wwpdb.apps.workmanager - import webapp"""

__docformat__ = "restructuredtext en"
__author__ = "Ezra Peisach"
__email__ = "peisach@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.01"

import sys
import unittest

if __package__ is None or __package__ == "":
    from os import path

    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    from commonsetup import TESTOUTPUT  # noqa:  F401 pylint: disable=import-error,unused-import
else:
    from .commonsetup import TESTOUTPUT  # noqa: F401

from wwpdb.apps.workmanager.webapp.WorkManagerWebApp import WorkManagerWebApp  # noqa: F401 pylint: disable=unused-import


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        pass


if __name__ == '__main__':
    unittest.main()
