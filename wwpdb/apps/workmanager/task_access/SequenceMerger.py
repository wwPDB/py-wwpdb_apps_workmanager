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

import os
import sys

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass


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
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self._getReturnMessage(self.__entryList, "_SequenceMerger", "Merge sequence information for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_SequenceMerger")
        if modelFile:
            updatedModelFile = self.__updateModelFile(entry_id, modelFile)
            if updatedModelFile:
                self._copyFileToArchiveDirectory(updatedModelFile, entry_id, "model", "pdbx", "next", "_SequenceMerger")
            #
        #

    def __updateModelFile(self, entry_id, inputFile):
        updatedModelFile = entry_id + "_SequenceMerger.cif"
        self._removeFile(os.path.join(self._sessionPath, updatedModelFile))
        logFile = "SequenceMerger_update_cif_" + entry_id + ".log"
        clogFile = "SequenceMerger_update_cif_command_" + entry_id + ".log"
        option = " -example " + self.__templateFile
        mismatch_flag = str(self._reqObj.getValue("mismatch_flag"))
        if mismatch_flag:
            option += " -rename "
        #
        cmd = self._getCmd("${BINPATH}/MergePolySeqInfo", inputFile, updatedModelFile, logFile, clogFile, option)
        self._runCmd(cmd)
        #
        msg = self._getLogMessage(os.path.join(self._sessionPath, logFile))
        cmsg = self._getLogMessage(os.path.join(self._sessionPath, clogFile))
        if cmsg:
            if msg:
                msg += "\n"
            #
            msg += cmsg
        #
        if msg:
            self._dumpPickle(entry_id + "_SequenceMerger", msg)
            return ""
        #
        if os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            return os.path.join(self._sessionPath, updatedModelFile)
        else:
            self._dumpPickle(entry_id + "_SequenceMerger", "Merge sequence information failed.")
            return ""
        #
