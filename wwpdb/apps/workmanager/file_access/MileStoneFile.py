##
# File:  MileStoneFile.py
# Date:  18-May-2015
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

# from mmcif_utils.trans.InstanceMapper       import InstanceMapper
# from wwpdb.utils.config.ConfigInfo import ConfigInfo
# from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppEm
from wwpdb.io.file.DataExchange import DataExchange
from wwpdb.io.locator.PathInfo import PathInfo


class MileStoneFile(object):
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
        self.__inputFile = ''
        # self.__isEmEntry = False
        # self.__sessionFile = ''
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)

    def setEmEntry(self):
        """
        """
        # self.__isEmEntry = True
        pass  # We do not care anymore - but leave API  pylint: disable=unnecessary-pass

    def getInputFile(self, entryId, source, content, format, version):  # pylint: disable=redefined-builtin
        """
        """
        sourcePath = self.__pI.getFilePath(dataSetId=entryId, wfInstanceId=None, contentType=content, formatType=format,
                                           fileSource=source, versionId=version, partNumber='1')
        if os.access(sourcePath, os.F_OK):
            self.__inputFile = sourcePath
            return True
        #
        return False

    def getOutputFile(self, entryId, source, content, format, version):  # pylint: disable=redefined-builtin
        """
        """
        if not self.__inputFile:
            return False
        #
        # if self.__isEmEntry:
        #     self.__cIA=ConfigInfoAppEm(self.__siteId)
        #     im = InstanceMapper(verbose=self.__verbose, log=self.__lfh)
        #     im.setMappingFilePath(self.__cIA.get_emd_mapping_file_path())
        #     self.__sessionFile = os.path.join(self.__sessionPath, entryId + '.emd.cif')
        #     im.translate(self.__inputFile, self.__sessionFile, mode="src-dst")
        #
        dE = DataExchange(reqObj=self.__reqObj, depDataSetId=entryId, fileSource=source, verbose=self.__verbose, log=self.__lfh)
        # if self.__sessionFile and os.access(self.__sessionFile, os.F_OK):
        #     dE.export(self.__sessionFile, contentType=content, formatType=format, version=version)
        # else:
        dE.export(self.__inputFile, contentType=content, formatType=format, version=version)
        #
        sourcePath = self.__pI.getFilePath(dataSetId=entryId, wfInstanceId=None, contentType=content, formatType=format,
                                           fileSource=source, versionId='latest', partNumber='1')
        if os.access(sourcePath, os.F_OK):
            return True
        #
        return False
