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

import os
import sys

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass


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
        self._setupGroupTaskPickle()
        #
        if "loi" in self.__taskList:
            self.__getLOIMap()
        #
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self.__loiMsg + self._getReturnMessage(self.__entryList, "_MetaDataMerger", "Merge meta data for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_MetaDataMerger")
        if modelFile:
            if self.__recoverFlag:
                if "revision" in self.__taskList:
                    templateFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model-release", "pdbx", "latest", "_MetaDataMerger")
                else:
                    templateFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "1", "_MetaDataMerger")
                #
                updatedModelFile = self.__updateModelFile(entry_id, modelFile, templateFile)
            else:
                updatedModelFile = self.__updateModelFile(entry_id, modelFile, self.__templateFile)
            #
            if updatedModelFile:
                self._copyFileToArchiveDirectory(updatedModelFile, entry_id, "model", "pdbx", "next", "_MetaDataMerger")
            #
        #

    def __updateModelFile(self, entry_id, inputFile, templateFile):
        """
        """
        filePathList = []
        updatedModelFile = entry_id + "_MetaDataMerger.cif"
        filePathList.append(os.path.join(self._sessionPath, updatedModelFile))
        logFile = "MetaDataMerger_update_cif_" + entry_id + ".log"
        filePathList.append(os.path.join(self._sessionPath, logFile))
        clogFile = "MetaDataMerger_update_cif_command_" + entry_id + ".log"
        filePathList.append(os.path.join(self._sessionPath, clogFile))
        #
        for filePath in filePathList:
            self._removeFile(filePath)
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
        defaultErrMsg = ""
        if not os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            defaultErrMsg = "Merge meta data failed."
        #
        if self._processLogMessage(entry_id + "_MetaDataMerger", filePathList[1:], defaultErrMsg):
            return os.path.join(self._sessionPath, updatedModelFile)
        else:
            return ""
        #
