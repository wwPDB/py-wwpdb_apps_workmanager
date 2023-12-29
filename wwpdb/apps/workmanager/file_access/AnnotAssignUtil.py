##
# File:  AnnotAssignUtil.py
# Date:  09-June-2015
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2015 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import os
import sys

from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.io.locator.PathInfo import PathInfo


class AnnotAssignUtil(object):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__lfh = log
        self.__verbose = verbose
        self.__sObj = self.__reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)

    def updateAnnotatorAssignment(self, assignList=None):
        """
        """
        if not assignList:
            return
        #
        for alist in assignList:
            sourcePath = self.__pI.getFilePath(dataSetId=alist[0], wfInstanceId=None, contentType='model', formatType='pdbx',
                                               fileSource='archive', versionId='latest', partNumber='1')
            if not sourcePath or not os.access(sourcePath, os.F_OK):
                continue
            #
            cifObj = mmCIFUtil(filePath=sourcePath)
            cifObj.UpdateSingleRowValue('pdbx_database_status', 'pdbx_annotator', 0, alist[1].upper())
            cifObj.WriteCif(outputFilePath=sourcePath)
        #
