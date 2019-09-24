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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import multiprocessing, os, sys

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass
from rcsb.utils.multiproc.MultiProcUtil               import MultiProcUtil
#

class CifChecker(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False,log=sys.stderr):
        """
        """
        super(CifChecker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__dictRoot  = self._cI.get('SITE_PDBX_DICT_PATH')
        self.__dictName  = self._cI.get('SITE_PDBX_DICT_NAME') + '.sdb'

    def run(self):
        """
        """
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose = True)
        mpu.set(workerObj = self, workerMethod = "runMulti")
        mpu.setWorkingDir(self._sessionPath)
        ok,failList,retLists,diagList = mpu.runMulti(dataList = self.__entryList, numProc = numProc, numResults = 1)
        return self.__getReturnMessage()

    def runMulti(self, dataList, procName, optionsD, workingDir):
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runSingle(entry_id)
            rList.append(entry_id)
        #
        return rList,rList,[]

    def __runSingle(self, entry_id):
        all_message = ''
        message,modelFile = self._getExistingArchiveFile(entry_id, 'model', 'pdbx', 'latest')
        if message:
            self._dumpPickle(entry_id + "_CifChecker", message)
            return
        #
        message = self.__checkModelFile(entry_id, modelFile)
        if message:
            self._dumpPickle(entry_id + "_CifChecker", message)
        else:
            self._dumpPickle(entry_id + "_CifChecker", 'OK')
        #

    def __checkModelFile(self, entry_id, inputFile):
        localModelFile = entry_id + "_CifChecker.cif"
        self._removeFile(os.path.join(self._sessionPath, localModelFile))
        message = self._copyFileUtil(inputFile, os.path.join(self._sessionPath, localModelFile))
        if message:
            return message
        #
        logFile = localModelFile + '-diag.log'
        self._removeFile(os.path.join(self._sessionPath, logFile))
        
        logFile = 'CifChecker_check_cif_' + entry_id + '.log'
        self._removeFile(os.path.join(self._sessionPath, logFile))
        clogFile = 'CifChecker_check_cif_command_' + entry_id + '.log'
        options = ' -dictSdb ' + os.path.join(self.__dictRoot, self.__dictName) + ' -f ' + localModelFile
        cmd = self._getCmd('${DICTBINPATH}/CifCheck', '', '', '', clogFile, options)
        self._runCmd(cmd)
        self._removeFile(os.path.join(self._sessionPath, localModelFile))
        self._removeFile(os.path.join(self._sessionPath, clogFile))
        return ''

    def __getReturnMessage(self):
        message = ''
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + "_CifChecker")
            error = ''
            if pickleData and pickleData != 'OK':
                error = pickleData + "\n"
            #
            logFile = os.path.join(self._sessionPath, entry_id + "_CifChecker.cif-diag.log")
            if os.access(logFile, os.F_OK):
                f = file(logFile, "r")
                error += f.read() + "\n"
                f.close()
            #
            if error:
                message += "Cif check for " + entry_id + ":\n" + error
            else:
                message += "Cif check for " + entry_id + " OK.\n"
            #
            self._removePickle(entry_id + "_CifChecker")
        #
        return message

if __name__ == '__main__':
    from wwpdb.utils.rcsb.WebRequest import InputRequest
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose = True, log = sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002030")
    myReqObj.setValue("sessionid", "88626e0cc0b1a1bbd10bb2df8a0d68573fcbd5fe")
    entryList = [ 'D_8000210285', 'D_8000210286' ]
    checkUtil = CifChecker(reqObj=myReqObj, entryList=entryList, verbose=False,log=sys.stderr)
    print(checkUtil.run())
