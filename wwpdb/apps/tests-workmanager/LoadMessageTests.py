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

import unittest

from wwpdb.apps.workmanager.utils.LoadRemindMessageTrack import LoadRemindMessageTrack  # noqa: F401


class ImportTests(unittest.TestCase):
    def setUp(self):
        pass

    def testInstantiate(self):
        pass


if __name__ == '__main__':
    unittest.main()
