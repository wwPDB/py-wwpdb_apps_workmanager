##
# File:  SequenceMerger.py
# Date:  30-May-2017
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2017 wwPDB

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


class SequenceMerger(BaseClass):
    def __init__(self, reqObj=None, entryList=None, templateFile=None, verbose=False, log=sys.stderr):
        """
        """
        super(SequenceMerger, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__templateFile = templateFile

    def run(self):
        """
        """
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
        message, modelFile = self._getExistingArchiveFile(entry_id, 'model', 'pdbx', 'latest')
        if message:
            self._dumpPickle(entry_id + "_SequenceMerger", message)
            return
        #
        message, updatedModelFile = self.__updateModelFile(entry_id, modelFile)
        if message:
            self._dumpPickle(entry_id + "_SequenceMerger", message)
            return
        #
        archiveModelFile = self._findArchiveFileName(entry_id, 'model', 'pdbx', 'next')
        message = self._copyFileUtil(updatedModelFile, archiveModelFile)
        if message:
            self._dumpPickle(entry_id + "_SequenceMerger", message)
        else:
            self._dumpPickle(entry_id + "_SequenceMerger", 'OK')
        #

    def __updateModelFile(self, entry_id, inputFile):
        updatedModelFile = entry_id + "_SequenceMerger.cif"
        self._removeFile(os.path.join(self._sessionPath, updatedModelFile))
        logFile = 'SequenceMerger_update_cif_' + entry_id + '.log'
        clogFile = 'SequenceMerger_update_cif_command_' + entry_id + '.log'
        option = ' -example ' + self.__templateFile
        mismatch_flag = str(self._reqObj.getValue("mismatch_flag"))
        if mismatch_flag:
            option += ' -rename '
        #
        cmd = self._getCmd('${BINPATH}/MergePolySeqInfo', inputFile, updatedModelFile, logFile, clogFile, option)
        self._runCmd(cmd)
        #
        msg = self._getLogMessage(os.path.join(self._sessionPath, logFile))
        cmsg = self._getLogMessage(os.path.join(self._sessionPath, clogFile))
        if cmsg:
            if msg:
                msg += '\n'
            #
            msg += cmsg
        #
        if msg:
            return msg, ""
        #
        if os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            return '', os.path.join(self._sessionPath, updatedModelFile)
        #
        return "Merge sequence information failed.", ""

    def __getReturnMessage(self):
        message = ''
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + "_SequenceMerger")
            if pickleData and pickleData != 'OK':
                message += "Merge sequence information for " + entry_id + " failed:\n\t" + pickleData + "\n"
            else:
                message += "Merge sequence information for " + entry_id + " successfully.\n"
            #
            self._removePickle(entry_id + "_SequenceMerger")
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
    myReqObj.setValue("sessionid", "fc3d934eb200f2f817eb1a8f2c608640cd3b1ba1")
    myEntryList = ['D_8000210285', 'D_8000210286']
    tempFile = '/wwpdb_da/da_top/data_test/archive/D_8000210285/D_8000210285_model_P1.cif.V10'
    pfGenUtil = SequenceMerger(reqObj=myReqObj, entryList=myEntryList, templateFile=tempFile, verbose=False, log=sys.stderr)
    print(pfGenUtil.run())
