##
# File:  LogFileUtil.py
# Date:  21-June-2015
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

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi


class LogFileUtil(object):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = str(self.__reqObj.getValue("WWPDB_SITE_ID"))
        self.__cI = ConfigInfo(self.__siteId)
        self.__depositionid = str(self.__reqObj.getValue("identifier"))
        self.__instanceid = str(self.__reqObj.getValue("instance"))
        self.__classid = str(self.__reqObj.getValue("classID"))
        self.__taskid = str(self.__reqObj.getValue("taskID"))
        self.__reference = str(self.__reqObj.getValue("reference"))
        self.__logPath = os.path.join(self.__cI.get('SITE_ARCHIVE_STORAGE_PATH'), 'archive', self.__depositionid, 'log')

    def getLogFile(self):
        """
        """
        if self.__taskid:
            filename = self.__reference + '_' + self.__depositionid + '_' + self.__classid + '_' + self.__instanceid \
                + '_' + self.__taskid + '.log'
        else:
            statusDB = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
            classInfo = statusDB.getWfClassByID(classID=self.__classid)
            filename = 'WFE_' + self.__depositionid + classInfo['class_file'][:-4] + '.log'
        #
        filePath = os.path.join(self.__logPath, filename)
        if os.access(filePath, os.F_OK):
            return filePath
        #
        return ''
