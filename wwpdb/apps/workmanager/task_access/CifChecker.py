##
# File:  CifChecker.py
# Date:  26-Apr-2017
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

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass
from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
#


class CifChecker(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(CifChecker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__dictRoot = os.path.abspath(self._cICommon.get_mmcif_dict_path())
        self.__dictName = self._cICommon.get_mmcif_archive_current_dict_filename() + ".sdb"
        self.__option = self._reqObj.getValue("option")
        #
        self.__optionDict = {"cifcheck" : ["CIF DICTIONARY", "_CifChecker", "_CifChecker.cif", "_CifChecker.cif-diag.log",
                                           "_CifChecker.log", "_CifChecker_cmd.log"],
                             "mischeck" : ["MISCELLANEOUS", "_MisChecker", "_MisChecker.cif", "_MiscChecking.txt",
                                           "_MisChecker.log", "_MisChecker_cmd.log"]}
        #

    def run(self):
        """
        """
        if (self.__option != "cifcheck") and (self.__option != "mischeck"):
            return "No task was defined!"
        #
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod="runMulti")
        mpu.setWorkingDir(self._sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=self.__entryList, numProc=numProc, numResults=1)
        return self.__getReturnMessage()

    def runMulti(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runSingle(entry_id)
            rList.append(entry_id)
        #
        return rList, rList, []

    def __runSingle(self, entry_id):
        message, modelFile = self._getExistingArchiveFile(entry_id, "model", "pdbx", "latest")
        if message:
            self._dumpPickle(entry_id + self.__optionDict[self.__option][1], message)
            return
        #
        message = self.__checkModelFile(entry_id, modelFile)
        if message:
            self._dumpPickle(entry_id + self.__optionDict[self.__option][1], message)
        else:
            self._dumpPickle(entry_id + self.__optionDict[self.__option][1], "OK")
        #

    def __checkModelFile(self, entry_id, inputFile):
        localModelFile = entry_id + self.__optionDict[self.__option][2]
        outputFile = entry_id + self.__optionDict[self.__option][3]
        logFile = entry_id + self.__optionDict[self.__option][4]
        clogFile = entry_id + self.__optionDict[self.__option][5]
        for fileName in (localModelFile, outputFile, logFile, clogFile):
            self._removeFile(os.path.join(self._sessionPath, fileName))
        #
        if self.__option == "cifcheck":
            message = self._copyFileUtil(inputFile, os.path.join(self._sessionPath, localModelFile))
            if message:
                return message
            #
            options = " -dictSdb " + os.path.join(self.__dictRoot, self.__dictName) + " -f " + localModelFile
            cmd = self._getCmd("${DICTBINPATH}/CifCheck", "", "", "", clogFile, options)
        else:
            cmd = self._getCmd("${BINPATH}/MiscChecking", inputFile, outputFile, logFile, clogFile, "")
        #
        self._runCmd(cmd)
        #
        for fileName in (localModelFile, logFile, clogFile):
            self._removeFile(os.path.join(self._sessionPath, fileName))
        #
        return ''

    def __getReturnMessage(self):
        message = ''
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + self.__optionDict[self.__option][1])
            error = ''
            if pickleData and pickleData != 'OK':
                error = pickleData + "\n"
            #
            logFile = os.path.join(self._sessionPath, entry_id + self.__optionDict[self.__option][3])
            if os.access(logFile, os.F_OK):
                f = open(logFile, "r")
                error += f.read() + "\n"
                f.close()
            #
            if error:
                message += self.__optionDict[self.__option][0] + " CHECK FOR " + entry_id + ":\n" + error
            else:
                message += self.__optionDict[self.__option][0] + " CHECK FOR " + entry_id + ": OK.\n"
            #
            self._removePickle(entry_id + self.__optionDict[self.__option][1])
        #
        return message


if __name__ == '__main__':
    from wwpdb.utils.session.WebRequest import InputRequest
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002030")
    myReqObj.setValue("sessionid", "88626e0cc0b1a1bbd10bb2df8a0d68573fcbd5fe")
    myentryList = ['D_8000210285', 'D_8000210286']
    checkUtil = CifChecker(reqObj=myReqObj, entryList=myentryList, verbose=False, log=sys.stderr)
    print(checkUtil.run())
