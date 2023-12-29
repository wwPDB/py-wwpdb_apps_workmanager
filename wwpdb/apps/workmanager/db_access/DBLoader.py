##
# File:  DBLoader.py
# Date:  01-Jul-2016
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2016 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import multiprocessing
import os
import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.utils.db.DBLoadUtil import DBLoadUtil
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
from wwpdb.io.locator.PathInfo import PathInfo
#


class DBLoader(object):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__entryList = entryList
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = str(self.__reqObj.getValue('WWPDB_SITE_ID'))
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        #
        self.__rcsbRoot = self.__cICommon.get_site_annot_tools_path()
        self.__compRoot = self.__cICommon.get_site_cc_cvs_path()
        #
        # self.__sessionId = None
        self.__sessionPath = None
        self.__getSession()
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        self.__returnMessage = ''

    def run(self):
        """
        """
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod="runMulti")
        mpu.setWorkingDir(self.__sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=self.__entryList, numProc=numProc, numResults=1)
        self.__runDBLoading()
        return self.__returnMessage

    def runMulti(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            sourceFile = self.__pI.getFilePath(dataSetId=entry_id, wfInstanceId=None, contentType='model', formatType='pdbx',
                                               fileSource='archive', versionId='latest', partNumber='1')
            if (not sourceFile) or (not os.access(sourceFile, os.F_OK)):
                continue
            #
            cmd = 'cd ' + self.__sessionPath + ' ; RCSBROOT=' + self.__rcsbRoot + ' ; export RCSBROOT ; COMP_PATH=' \
                + self.__compRoot + ' ; export COMP_PATH ; BINPATH=${RCSBROOT}/bin; export BINPATH; ${BINPATH}/GetDepositionInfo ' \
                + ' -input ' + sourceFile + ' -output ' + entry_id + '_db_info.cif -log ' + entry_id + '_db.log > ' + entry_id \
                + '_db_command.log  2>&1 ; '
            os.system(cmd)
            rList.append(entry_id)
        #
        return rList, rList, []

    def __runDBLoading(self):
        """
        """
        statusDB = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        file_list = []
        for entry_id in self.__entryList:
            sourceFile = self.__pI.getFilePath(dataSetId=entry_id, wfInstanceId=None, contentType='model', formatType='pdbx',
                                               fileSource='archive', versionId='latest', partNumber='1')
            if sourceFile and os.access(sourceFile, os.F_OK):
                file_list.append(sourceFile)
            #
            info_file = os.path.join(self.__sessionPath, entry_id + '_db_info.cif')
            if os.access(info_file, os.F_OK):
                cifObj = mmCIFUtil(filePath=info_file)
                vList = cifObj.GetValue('info')
                if vList:
                    info_data = vList[0]
                    if info_data:
                        self.__returnMessage += 'Loaded ' + entry_id + ' successfully.\n'
                        statusDB.runUpdate(table='deposition', where={'dep_set_id' : entry_id}, data=info_data)
                    else:
                        self.__returnMessage += 'Loading ' + entry_id + ' failed.\n'
                    #
                else:
                    self.__returnMessage += 'Loading ' + entry_id + ' failed.\n'
                #
            else:
                self.__returnMessage += 'Loading ' + entry_id + ' failed.\n'
            #
        #
        if file_list:
            dbLoader = DBLoadUtil(reqObj=self.__reqObj, verbose=self.__verbose, log=self.__lfh)
            dbLoader.doLoading(file_list)
        #

    def __getSession(self):
        """
        """
        self.__sObj = self.__reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()


if __name__ == '__main__':
    from wwpdb.utils.session.WebRequest import InputRequest
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002003")
    myReqObj.setValue("sessionid", " b8030220bdf3559c10a2c63618cd85a25256f7c1")
    myentryList = ['D_8000200175', 'D_8000200176']
    copyUtil = DBLoader(reqObj=myReqObj, entryList=myentryList, verbose=False, log=sys.stderr)
    print(copyUtil.run())
