##
# File:  RunValidationTask.py
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
import traceback

from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass
from wwpdb.utils.dp.ValidationWrapper import ValidationWrapper

class RunValidationTask(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(RunValidationTask, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList

    def run(self):
        """
        """
        # Set maximum parallel process#
        self._defaultNumProcess = 4
        #
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self._getReturnMessage(self.__entryList, "_RunValidationTask", "Run annotation task for ")

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
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", "_RunValidationTask")
        if modelFile:
            self.__runValidation(entry_id, modelFile)
        #

    def __runValidation(self, entry_id, inputFile):
        """
        """
        try:
            rundir = os.path.join(self._sessionPath, "LVW_" + entry_id.upper())
            self._removeDirectory(rundir)
            self._makeDirectory(rundir)
            #
            dp = ValidationWrapper(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            dp.imp(inputFile)
            dp.addInput(name="entry_id", value=entry_id)
            dp.addInput(name="run_dir", value=rundir)
            #
            hasSFile = False
            for inputExpFileTuple in ( ( "sf_file_path", "structure-factors", "pdbx" ), ( "cs_file_path", "nmr-data-str", "pdbx" ), \
                                       ( "nmr_restraint_file_path", "nmr-data-str", "pdbx" ), ( "vol_file_path", "em-volume", "map" ), \
                                       ( "fsc_file_path", "fsc", "xml" ) ):
                expFilePath = self._findArchiveFileName(entry_id, inputExpFileTuple[1], inputExpFileTuple[2], "latest")
                if (not expFilePath) and (inputExpFileTuple[0] == "cs_file_path"):
                    expFilePath = self._findArchiveFileName(entry_id, "nmr-chemical-shifts", "pdbx", "latest")
                #
                if expFilePath and os.access(expFilePath, os.F_OK):
                    dp.addInput(name=inputExpFileTuple[0], value=expFilePath)
                    if inputExpFileTuple[0] == "sf_file_path":
                        hasSFile = True
                    #
                #
            #
            dp.addInput(name="request_annotation_context", value="yes")
            dp.addInput(name="request_validation_mode", value="annotate")
            dp.op("annot-wwpdb-validate-all-sf")
            #
            outputFileList = []
            for reportFileTuple in ( ( "validation-report", "pdf" ), ( "validation-data", "xml" ), ( "validation-report-full", "pdf" ), \
                                     ( "validation-report-slider", "png" ), ( "validation-report-slider", "svg" ), \
                                     ( "validation-report-images", "tar" ), ( "validation-data", "pdbx" ), \
                                     ( "validation-report-fo-map-coef", "pdbx" ), ( "validation-report-2fo-map-coef", "pdbx" ) ):
                fName = self._pI.getFileName(entry_id, contentType=reportFileTuple[0], formatType=reportFileTuple[1], versionId="none", partNumber="1")
                outputFileList.append(os.path.join(self._sessionPath, fName))
            #
            logFilePath = os.path.join(self._sessionPath, entry_id + "_val-report.log")
            dp.expLog(logFilePath)
            dp.expList(dstPathList=outputFileList)
            dp.cleanup()
            #
            errMsg = ""
            for idx,reportFileTuple in enumerate( ( ( "validation-report", "pdf", "validation-report pdf", False ), \
                    ( "validation-data", "xml", "validation-data xml", False ), \
                    ( "validation-report-full", "pdf", "validation-report-full pdf", False ), \
                    ( "validation-report-slider", "png", "validation-report-slider png", False ), \
                    ( "validation-report-slider", "svg", "validation-report-slider svg", False ), \
                    ( "validation-report-images", "tar", "validation-report-images tar", False ), \
                    ( "validation-data", "pdbx", "validation-data cif", False ), \
                    ( "validation-report-fo-map-coef", "pdbx", "validation-report-fo-map-coef cif", True ), \
                    ( "validation-report-2fo-map-coef", "pdbx", "validation-report-2fo-map-coef cif", True ) ) ):
                if reportFileTuple[0] == "validation-report-images":
                    continue
                #
                if not os.access(outputFileList[idx], os.F_OK):
                    if reportFileTuple[3] and (not hasSFile):
                        continue
                    #
                    if errMsg:
                        errMsg += "\n"
                    #
                    errMsg += "Missing " + reportFileTuple[2] + " file.";
                    continue
                #
                archiveFilePath = self._findArchiveFileName(entry_id, reportFileTuple[0], reportFileTuple[1], "next")
                msg = self._copyFileUtil(outputFileList[idx], archiveFilePath)
                if msg:
                    if errMsg:
                        errMsg += "\n"
                    #
                    errMsg += msg
                #
            #
            if errMsg:
                self._dumpPickle(entry_id + "_RunValidationTask", errMsg)
            else:
                self._dumpPickle(entry_id + "_RunValidationTask", "OK")
            #
        except:  # noqa: E722 pylint: disable=bare-except
            self._dumpPickle(entry_id + "_RunValidationTask", traceback.format_exc())
            traceback.print_exc(file=self._lfh)
        #
