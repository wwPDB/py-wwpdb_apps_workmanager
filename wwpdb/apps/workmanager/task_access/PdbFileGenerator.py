##
# File:  PdbFileGenerator.py
# Date:  24-Apr-2017
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


class PdbFileGenerator(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(PdbFileGenerator, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList

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
            self._dumpPickle(entry_id + "_PdbFileGenerator", message)
            return
        #
        message, pdbFile = self.__generatePdbFile(entry_id, modelFile)
        if message:
            self._dumpPickle(entry_id + "_PdbFileGenerator", message)
            return
        #
        archivePdbFile = self._findArchiveFileName(entry_id, 'model', 'pdb', 'next')
        message = self._copyFileUtil(pdbFile, archivePdbFile)
        if message:
            self._dumpPickle(entry_id + "_PdbFileGenerator", message)
        else:
            self._dumpPickle(entry_id + "_PdbFileGenerator", 'OK')
        #

    def __generatePdbFile(self, entry_id, inputFile):
        pdbFile = entry_id + "_PdbFileGenerator.pdb"
        self._removeFile(os.path.join(self._sessionPath, pdbFile))
        logFile = 'PdbFileGenerator_generate_pdb_' + entry_id + '.log'
        clogFile = 'PdbFileGenerator_generate_pdb_command_' + entry_id + '.log'
        cmd = self._getCmd('${BINPATH}/maxit', inputFile, pdbFile, logFile, clogFile, ' -o 2 ')
        self._runCmd(cmd)
        if os.access(os.path.join(self._sessionPath, pdbFile), os.F_OK):
            return '', os.path.join(self._sessionPath, pdbFile)
        #
        return "Convert PDB file failed.", ""

    def __getReturnMessage(self):
        message = ''
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + "_PdbFileGenerator")
            if pickleData and pickleData != 'OK':
                message += "Generate PDB file for " + entry_id + " failed:\n\t" + pickleData + "\n"
            else:
                message += "Generate PDB file for " + entry_id + " successfully.\n"
            #
            self._removePickle(entry_id + "_PdbFileGenerator")
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
    pfGenUtil = PdbFileGenerator(reqObj=myReqObj, entryList=myentryList, verbose=False, log=sys.stderr)
    print(pfGenUtil.run())
