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

import os
import sys

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass

class PdbFileGenerator(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(PdbFileGenerator, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList

    def run(self):
        """
        """
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self._getReturnMessage(self.__entryList, "_PdbFileGenerator", "Generate PDB file for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_PdbFileGenerator")
        if modelFile:
            pdbFile = self.__generatePdbFile(entry_id, modelFile)
            if pdbFile:
                self._copyFileToArchiveDirectory(pdbFile, entry_id, "model", "pdb", "next", "_PdbFileGenerator")
            #
        #

    def __generatePdbFile(self, entry_id, inputFile):
        pdbFilePath = os.path.join(self._sessionPath, entry_id + "_PdbFileGenerator.pdb")
        logFilePath = os.path.join(self._sessionPath, "PdbFileGenerator_generate_pdb_" + entry_id + ".log")
        clogFilePath = os.path.join(self._sessionPath, "PdbFileGenerator_generate_pdb_command_" + entry_id + ".log")
        outputFileList = [ pdbFilePath, logFilePath, clogFilePath ]
        self._dpUtilityApi(operator="annot-get-pdb-file", inputFileName=inputFile, outputFilePathList=outputFileList, pickleFile=entry_id + "_PdbFileGenerator")
        #
        defaultErrMsg = ""
        if not os.access(pdbFilePath, os.F_OK):
            defaultErrMsg = "Convert PDB file failed."
        #
        if self._processLogMessage(entry_id + "_PdbFileGenerator", outputFileList[1:], defaultErrMsg):
            return pdbFilePath
        else:
            return ""
        #
