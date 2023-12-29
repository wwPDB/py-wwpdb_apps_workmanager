##
# File:  MetaDataMerger.py
# Date:  30-Mar-2020
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2020 wwPDB

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


class MetaDataMerger(BaseClass):
    def __init__(self, reqObj=None, entryList=None, taskList=None, recoverFlag=False, templateFile=None, verbose=False, log=sys.stderr):
        """
        """
        super(MetaDataMerger, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__taskList = taskList
        self.__recoverFlag = recoverFlag
        self.__templateFile = templateFile
        self.__loiMap = {}
        self.__loiMsg = ""

    def run(self):
        """
        """
        if "loi" in self.__taskList:
            self.__getLOIMap()
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

    def __getLOIMap(self):
        """
        """
        for entry_id in self.__entryList:
            ligList = self._reqObj.getValueList("ligand_" + entry_id)
            if ligList:
                self.__loiMap[entry_id] = ligList
            #
        #
        if not self.__loiMap:
            self.__loiMsg = "No ligand selected for 'Ligand of interesting' task.\n"
        #

    def __runSingle(self, entry_id):
        """
        """
        message, modelFile = self._getExistingArchiveFile(entry_id, "model", "pdbx", "latest")
        if message:
            self._dumpPickle(entry_id + "_MetaDataMerger", message)
            return
        #
        if self.__recoverFlag:
            if "revision" in self.__taskList:
                message, templateFile = self._getExistingArchiveFile(entry_id, "model-release", "pdbx", "latest")
            else:
                message, templateFile = self._getExistingArchiveFile(entry_id, "model", "pdbx", "1")
            #
            if message:
                self._dumpPickle(entry_id + "_MetaDataMerger", message)
                return
            #
            message, updatedModelFile = self.__updateModelFile(entry_id, modelFile, templateFile)
        else:
            message, updatedModelFile = self.__updateModelFile(entry_id, modelFile, self.__templateFile)
        #
        if message:
            self._dumpPickle(entry_id + "_MetaDataMerger", message)
            return
        #
        archiveModelFile = self._findArchiveFileName(entry_id, "model", "pdbx", "next")
        message = self._copyFileUtil(updatedModelFile, archiveModelFile)
        if message:
            self._dumpPickle(entry_id + "_MetaDataMerger", message)
        else:
            self._dumpPickle(entry_id + "_MetaDataMerger", "OK")
        #

    def __updateModelFile(self, entry_id, inputFile, templateFile):
        """
        """
        updatedModelFile = entry_id + "_MetaDataMerger.cif"
        self._removeFile(os.path.join(self._sessionPath, updatedModelFile))
        logFile = "MetaDataMerger_update_cif_" + entry_id + ".log"
        self._removeFile(os.path.join(self._sessionPath, logFile))
        clogFile = "MetaDataMerger_update_cif_command_" + entry_id + ".log"
        self._removeFile(os.path.join(self._sessionPath, clogFile))
        #
        option = " -task " + ",".join(self.__taskList)
        if templateFile:
            option += " -example " + templateFile
        #
        if (entry_id in self.__loiMap) and self.__loiMap[entry_id]:
            option += " -ligand " + ",".join(self.__loiMap[entry_id])
        #
        cmd = self._getCmd("${BINPATH}/MergeMetaDataApp", inputFile, updatedModelFile, logFile, clogFile, option)
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
            return msg, ""
        #
        if os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            return "", os.path.join(self._sessionPath, updatedModelFile)
        #
        return "Merge meta data failed.", ""

    def __getReturnMessage(self):
        message = self.__loiMsg
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + "_MetaDataMerger")
            if pickleData and pickleData != "OK":
                message += "Merge meta data for " + entry_id + " failed:\n\t" + pickleData + "\n"
            else:
                message += "Merge meta data for " + entry_id + " successfully.\n"
            #
            self._removePickle(entry_id + "_MetaDataMerger")
        #
        return message
