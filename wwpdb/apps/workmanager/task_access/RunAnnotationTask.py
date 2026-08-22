##
# File:  RunAnnotationTask.py
# Date:  23-Jun-2026
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

import os
import sys

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass


class RunAnnotationTask(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(RunAnnotationTask, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList

    def run(self):
        """
        """
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self._getReturnMessage(self.__entryList, "_RunAnnotationTask", "Run annotation task for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_RunAnnotationTask")
        if modelFile:
            updatedModelFile = self.__runAnnotation(entry_id, modelFile)
            if updatedModelFile:
                self._copyFileToArchiveDirectory(updatedModelFile, entry_id, "model", "pdbx", "next", "_RunAnnotationTask")
            #
        #

    def __runAnnotation(self, entry_id, inputFile):
        cifFilePath = os.path.join(self._sessionPath, entry_id + "_RunAnnotationTask.cif")
        logFilePath = os.path.join(self._sessionPath, "RunAnnotationTask_" + entry_id + ".log")
        clogFilePath = os.path.join(self._sessionPath, "RunAnnotationTask_command_" + entry_id + ".log")
        outputFileList = [cifFilePath, logFilePath, clogFilePath]
        self._dpUtilityApi(operator="annot-consolidated-tasks", inputFileName=inputFile, outputFilePathList=outputFileList, pickleFile=entry_id + "_RunAnnotationTask")
        #
        defaultErrMsg = ""
        if not os.access(cifFilePath, os.F_OK):
            defaultErrMsg = "Run annotation task failed."
        #
        if self._processLogMessage(entry_id + "_RunAnnotationTask", outputFileList[1:], defaultErrMsg):
            return cifFilePath
        else:
            return ""
        #
