##
# File:  RunLigandTask.py
# Date:  25-Jun-2026
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
import traceback

from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass

class RunLigandTask(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(RunLigandTask, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList

    def run(self):
        """
        """
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self._getReturnMessage(self.__entryList, "_RunLigandTask", "Run ligand task for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_RunLigandTask")
        if modelFile:
            self.__runLigand(entry_id, modelFile)
        #

    def __runLigand(self, entry_id, inputFile):
        """
        """
        try:
            entryDirPath = os.path.join(self._sessionPath, entry_id)
            self._removeDirectory(entryDirPath)
            self._makeDirectory(entryDirPath)
            #
            ccLinkPath = os.path.join(entryDirPath, entry_id + "-link.cif")
            self._dpUtilityApi(operator="chem-comp-link", inputFileName=inputFile, outputFilePath=ccLinkPath, pickleFile=entry_id + "_RunLigandTask")
            #
            ccAssignPath = os.path.join(entryDirPath, entry_id + "-assign.cif") 
            additionalOptions = {}
            if os.access(ccLinkPath, os.F_OK):
                additionalOptions["cc_link_file_path"] = ( ccLinkPath, "file" )
            #
            additionalOptions["id"] = ( entry_id, "param" )
            self._dpUtilityApi(operator="chem-comp-assign", inputFileName=inputFile, outputFilePath=ccAssignPath, options=additionalOptions, \
                               WorkingDir=entryDirPath, pickleFile=entry_id + "_RunLigandTask", cleanUp=False)
            #
            if not os.access(ccAssignPath, os.F_OK):
                self._dumpPickle(entry_id + "_RunLigandTask", "Missing 'chem-comp-assign' cif file.")
                return
            #
            readIoObj = IoAdapter()
            cifContainerList = readIoObj.readFile(ccAssignPath)
            if len(cifContainerList) == 0:
                self._dumpPickle(entry_id + "_RunLigandTask", "Read 'chem-comp-assign' cif file failed.")
                return
            #
            catObj = cifContainerList[0].getObj("pdbx_entry_info")
            if not catObj:
                self._dumpPickle(entry_id + "_RunLigandTask", "Read 'chem-comp-assign' cif file failed.")
                return
            #
            status = self.__getValue(catObj, "status", 0)
            if status == "No ligand found":
                self._dumpPickle(entry_id + "_RunLigandTask", "OK: the entry does not contain ligands.")
                return
            #
            autoFlag = False
            if status == "OK":
                autoFlag = True
            #
            if not autoFlag:
                self._dumpPickle(entry_id + "_RunLigandTask", "The entry needs to be reviwed in LigMod.")
                return
            #
            additionalOptions = {}
            additionalOptions["cc_assign_file_path"] = ( ccAssignPath, "file" )
            updatedModelFilePath = os.path.join(entryDirPath, entry_id + "_updated.cif")
            logFilePath = os.path.join(entryDirPath, "RunLigandTask_" + entry_id + ".log")
            clogFilePath = os.path.join(entryDirPath, "RunLigandTask_command_" + entry_id + ".log")
            outputFileList = [ updatedModelFilePath, logFilePath, clogFilePath ]
            self._dpUtilityApi(operator="chem-comp-instance-update", inputFileName=inputFile, outputFilePathList=outputFileList, \
                               options=additionalOptions, pickleFile=entry_id + "_RunLigandTask")
            #
            defaultErrMsg = ""
            if not os.access(updatedModelFilePath, os.F_OK):
                defaultErrMsg = "Run ligand task failed."
            #
            if self._processLogMessage(entry_id + "_RunLigandTask", outputFileList[1:], defaultErrMsg):
                self._copyFileToArchiveDirectory(updatedModelFilePath, entry_id, "model", "pdbx", "next", "_RunLigandTask")
            #
        except:  # noqa: E722 pylint: disable=bare-except
            self._dumpPickle(entry_id + "_RunLigandTask", traceback.format_exc())
            traceback.print_exc(file=self._lfh)
        #

    def __getValue(self, catObj, attribute, rowIdx):
        """ Get a value from attributeName='attribute', rowIndex='rowIdx' in catetory object 'catObj'.
        """
        value = ""
        try:
            value = catObj.getValue(attributeName=attribute, rowIndex=rowIdx)
            if (value is None) or (value == ".") or (value == "?"):
                value = ""
            #
            value = value.strip()
        except:
            value = ""
        #
        return value
