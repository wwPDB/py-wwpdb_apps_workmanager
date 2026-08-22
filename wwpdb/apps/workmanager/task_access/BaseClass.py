##
# File:  BaseClass.py
# Date:  24-Apr-2017
# Updates:
##
"""
Base class for handle all workflow manager task activities

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
__version__ = "V1.00"

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import filecmp
import multiprocessing
import os
import shutil
import sys
import time
import traceback

from datetime import datetime

from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
from wwpdb.io.locator.PathInfo import PathInfo
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.utils.dp.RcsbDpUtility import RcsbDpUtility


class BaseClass(object):
    """ Base Class responsible for all workflow manager task activities
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        self._verbose = verbose
        self._lfh = log
        self._reqObj = reqObj
        self._sObj = None
        self._sessionId = None
        self._sessionPath = None
        self._siteId = str(self._reqObj.getValue("WWPDB_SITE_ID"))
        self._cI = ConfigInfo(self._siteId)
        self._cICommon = ConfigInfoAppCommon(self._siteId)
        self._archivePath = self._cI.get("SITE_ARCHIVE_STORAGE_PATH")
        #
        self._start_time = None
        self._groupTaskPickleFile = None
        #
        self._defaultNumProcess = 0
        #
        self._pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)
        #
        self.__getSession()

    def getGroupTaskInfo(self):
        """ Get group task information
        """
        groupId = self._reqObj.getValue("identifier")
        if (groupId is None) or (groupId == ""):
            return {}
        #
        groupDirPath = os.path.join(self._archivePath, "autogroup", groupId)
        if not os.access(groupDirPath, os.F_OK):
            return {}
        #
        self._groupTaskPickleFile = os.path.join(groupDirPath, groupId + "-task.pickle")
        return self.__loadGroupTaskPickle()

    def getMessage(self):
        """ Get group task log message based on task key
        """
        message = "Something goes wrong!"
        groupId = self._reqObj.getValue("identifier")
        taskKey = self._reqObj.getValue("task_key")
        if (groupId is None) or (groupId == "") or (taskKey is None) or (taskKey == ""):
            return message
        #
        groupDirPath = os.path.join(self._archivePath, "autogroup", groupId)
        if not os.access(groupDirPath, os.F_OK):
            return message
        #
        self._groupTaskPickleFile = os.path.join(groupDirPath, groupId + "-task.pickle")
        #
        pickleObj = self.__loadGroupTaskPickle()
        if (taskKey in pickleObj) and pickleObj[taskKey] and ("message" in pickleObj[taskKey]) and pickleObj[taskKey]["message"]:
            message = pickleObj[taskKey]["message"]
        #
        return message

    def removeMessage(self):
        """ Remove group task log message based on task key
        """
        message = "Something goes wrong!"
        groupId = self._reqObj.getValue("identifier")
        taskKey = self._reqObj.getValue("task_key")
        if (groupId is None) or (groupId == "") or (taskKey is None) or (taskKey == ""):
            return message
        #
        groupDirPath = os.path.join(self._archivePath, "autogroup", groupId)
        if not os.access(groupDirPath, os.F_OK):
            return message
        #
        self._groupTaskPickleFile = os.path.join(groupDirPath, groupId + "-task.pickle")
        #
        pickleObj = self.__loadGroupTaskPickle()
        if taskKey in pickleObj:
            del pickleObj[taskKey]
            self.__dumpGroupTaskPickle(pickleObj)
            message = "OK"
        #
        return message

    def _runMultiProcess(self, classMethod=None, inputDataList=None):
        """ General method to run multiprocessing with MultiProcPoolUtil wrapper class.
            classMethod: the interface method for multiprocessing module that executes the processing.
            inputDataList: input data list
        """
        if inputDataList is None:
            inputDataList = []
        numProcess = int(multiprocessing.cpu_count() / 2)
        if numProcess == 0:
            if self._defaultNumProcess > 1:
                self._defaultNumProcess = 1
            #
            numProcess = 1
        #
        if numProcess > len(inputDataList):
            numProcess = len(inputDataList)
        #
        if (self._defaultNumProcess > 0) and (numProcess > self._defaultNumProcess):
            numProcess = self._defaultNumProcess
        #
        chunksize = 0
        if int(len(inputDataList) / numProcess) > 10:
            chunksize = 10
        #
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod=classMethod)
        mpu.setWorkingDir(self._sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=inputDataList, numProc=numProcess, numResults=1, chunkSize=chunksize)

    def _setupGroupTaskPickle(self):
        """ Setup group task pickle file for tracking task running status
        """
        groupId = self._reqObj.getValue("identifier")
        taskLabel = self._reqObj.getValue("button_label")
        if (groupId is None) or (groupId == "") or (taskLabel is None) or (taskLabel == ""):
            return
        #
        groupDirPath = os.path.join(self._archivePath, "autogroup", groupId)
        if not os.access(groupDirPath, os.F_OK):
            return
        #
        self._start_time = str(time.time())
        self._groupTaskPickleFile = os.path.join(groupDirPath, groupId + "-task.pickle")
        #
        pickObj = self.__loadGroupTaskPickle()
        #
        taskObj = {}
        taskObj["task_id"] = taskLabel
        taskObj["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        taskObj["status"] = "running"
        pickObj[self._start_time] = taskObj
        #
        self.__dumpGroupTaskPickle(pickObj)

    def _getReturnMessage(self, entryList, pickleSuffix, messageHead):
        """ Get each entry's process message from pickle file.
        """
        message = ""
        for entry_id in entryList:
            pickleData = self._loadPickle(entry_id + pickleSuffix)
            if pickleData and pickleData != "OK":
                message += messageHead + entry_id + " failed:\n\t" + pickleData + "\n"
            else:
                message += messageHead + entry_id + " successfully.\n"
            #
            self._removePickle(entry_id + pickleSuffix)
        #
        self._updateGroupTaskPickle(message)
        #
        return message

    def _updateGroupTaskPickle(self, message):
        pickObj = self.__loadGroupTaskPickle()
        #
        if self._start_time not in pickObj:
            return
        #
        pickObj[self._start_time]["status"] = "finished"
        pickObj[self._start_time]["message"] = message
        pickObj[self._start_time]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        #
        self.__dumpGroupTaskPickle(pickObj)

    def _getExistingArchiveFile(self, entryId, contentType, formatType, version):
        filePath = self._findArchiveFileName(entryId, contentType, formatType, version)
        message = ""
        if not filePath:
            message = "Can not find " + version + " " + contentType + " " + formatType + " file."
        elif not os.access(filePath, os.F_OK):
            message = "File " + filePath + " does not exist."
        #
        return message, filePath

    def _getExistingArchiveFileWithPickleMessage(self, entryId, contentType, formatType, version, pickleSuffix):
        filePath = self._findArchiveFileName(entryId, contentType, formatType, version)
        if not filePath:
            self._dumpPickle(entryId + pickleSuffix, "Can not find " + version + " " + contentType + " " + formatType + " file.")
            return ""
        elif not os.access(filePath, os.F_OK):
            self._dumpPickle(entryId + pickleSuffix, "File " + filePath + " does not exist.")
            return ""
        #
        return filePath

    def _dpUtilityApi(self, operator="", inputFileName="", outputFilePath="", outputFilePathList=None, options=None, WorkingDir=None, pickleFile="", cleanUp=True):
        if options is None:
            options = {}
        if outputFilePathList is None:
            outputFilePathList = []

        if (not operator) or (not inputFileName) or ((outputFilePath == "") and (len(outputFilePathList) == 0)):
            return
        #
        if (outputFilePath != "") and os.access(outputFilePath, os.F_OK):
            os.remove(outputFilePath)
        #
        if len(outputFilePathList) > 0:
            for outputPath in outputFilePathList:
                if os.access(outputPath, os.F_OK):
                    os.remove(outputPath)
                #
            #
        #
        try:
            dp = RcsbDpUtility(tmpPath=self._sessionPath, siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            if WorkingDir is not None:
                dp.setWorkingDir(WorkingDir)
            #
            if len(options) > 0:
                for key, valtypeTupl in options.items():
                    dp.addInput(name=key, value=valtypeTupl[0], type=valtypeTupl[1])
                #
            #
            dp.imp(inputFileName)
            dp.op(operator)
            #
            if outputFilePath != "":
                dp.exp(outputFilePath)
            elif len(outputFilePathList) > 0:
                dp.expList(dstPathList=outputFilePathList)
            #
            if cleanUp:
                dp.cleanup()
            #
        except:  # noqa: E722 pylint: disable=bare-except
            self._dumpPickle(pickleFile, traceback.format_exc())
            traceback.print_exc(file=self._lfh)
        #

    def _findArchiveFileName(self, entryId, contentType, formatType, version):
        return self._pI.getFilePath(dataSetId=entryId, wfInstanceId=None, contentType=contentType, formatType=formatType,
                                    fileSource="archive", versionId=version, partNumber="1")

    def _copyFileUtil(self, sourcePath, targetPath):
        if not sourcePath:
            return "Copying file: No source file defined."
        #
        if not targetPath:
            return "Copying file: No target file defined."
        #
        if not os.access(sourcePath, os.F_OK):
            return "File '" + sourcePath + "' not found."
        #
        shutil.copyfile(sourcePath, targetPath)
        if not os.access(targetPath, os.F_OK):
            return "copying '" + sourcePath + "' to '" + targetPath + "' failed."
        elif not filecmp.cmp(sourcePath, targetPath):
            return "copying '" + sourcePath + "' to '" + targetPath + "' failed."
        #
        return ""

    def _copyFileToArchiveDirectory(self, sourcePath, entryId, contentType, formatType, version, pickleSuffix):
        if not sourcePath:
            self._dumpPickle(entryId + pickleSuffix, "Copying file: No source file defined.")
            return
        #
        if not os.access(sourcePath, os.F_OK):
            self._dumpPickle(entryId + pickleSuffix, "File '" + sourcePath + "' not found.")
            return
        #
        targetPath = self._findArchiveFileName(entryId, contentType, formatType, version)
        if not targetPath:
            self._dumpPickle(entryId + pickleSuffix, "Copying file: No target file defined.")
            return
        #
        shutil.copyfile(sourcePath, targetPath)
        if not os.access(targetPath, os.F_OK):
            self._dumpPickle(entryId + pickleSuffix, "copying '" + sourcePath + "' to '" + targetPath + "' failed.")
        elif not filecmp.cmp(sourcePath, targetPath):
            self._dumpPickle(entryId + pickleSuffix, "copying '" + sourcePath + "' to '" + targetPath + "' failed.")
        else:
            self._dumpPickle(entryId + pickleSuffix, "OK")
        #

    def _bashSetting(self):
        setting = " RCSBROOT=" + self._cICommon.get_site_annot_tools_path() + "; export RCSBROOT; " \
            + " COMP_PATH=" + self._cICommon.get_site_cc_cvs_path() + "; export COMP_PATH; " \
            + " BINPATH=${RCSBROOT}/bin; export BINPATH; " \
            + " LOCALBINPATH=" + os.path.join(self._cICommon.get_site_local_apps_path(), "bin") + "; export LOCALBINPATH; " \
            + " DICTBINPATH=" + os.path.join(self._cICommon.get_site_packages_path(), "dict", "bin") + "; export DICTBINPATH; "
        return setting

    def _getCmd(self, command, inputFile, outputFile, logFile, clogFile, extraOptions):
        cmd = "cd " + self._sessionPath + " ; " + self._bashSetting() + " " + command
        if inputFile:
            cmd += " -input " + inputFile
        #
        if outputFile:
            if outputFile != inputFile:
                self._removeFile(os.path.join(self._sessionPath, outputFile))
            #
            cmd += " -output " + outputFile
        #
        if extraOptions:
            cmd += " " + extraOptions
        #
        if logFile:
            self._removeFile(os.path.join(self._sessionPath, logFile))
            cmd += " -log " + logFile
        #
        if clogFile:
            self._removeFile(os.path.join(self._sessionPath, clogFile))
            cmd += " > " + clogFile + " 2>&1"
        #
        cmd += " ; "
        return cmd

    def _runCmd(self, cmd):
        # self._lfh.write("running cmd=%s\n" % cmd)
        os.system(cmd)

    def _removeFile(self, filePath):
        if os.access(filePath, os.F_OK):
            os.remove(filePath)
        #

    def _removeDirectory(self, dirPath):
        """ Remove a directory if it exists.
        """
        if os.access(dirPath, os.F_OK):
            shutil.rmtree(dirPath)
        #

    def _makeDirectory(self, dirPath):
        """ Make a directory if it does not exist.
        """
        if not os.access(dirPath, os.F_OK):
            os.makedirs(dirPath)
        #

    def _dumpPickle(self, pickleFile, pickleData):
        fb = open(os.path.join(self._sessionPath, pickleFile + ".pickle"), "wb")
        pickle.dump(pickleData, fb)
        fb.close()

    def _loadPickle(self, pickleFile):
        picklePath = os.path.join(self._sessionPath, pickleFile + ".pickle")
        if not os.access(picklePath, os.F_OK):
            return None
        #
        fb = open(picklePath, "rb")
        pickleData = pickle.load(fb)
        fb.close()
        return pickleData

    def _removePickle(self, pickleFile):
        self._removeFile(os.path.join(self._sessionPath, pickleFile + ".pickle"))

    def _processTemplate(self, fn, parameterDict=None):
        """ Read the input HTML template data file and perform the key/value substitutions in the
            input parameter dictionary.

            :Params:
                ``parameterDict``: dictionary where
                key = name of subsitution placeholder in the template and
                value = data to be used to substitute information for the placeholder

            :Returns:
                string representing entirety of content with subsitution placeholders now replaced with data
        """
        if parameterDict is None:
            parameterDict = {}
        tPath = self._reqObj.getValue("TemplatePath")
        fPath = os.path.join(tPath, fn)
        ifh = open(fPath, "r")
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)

    def _getLogMessage(self, logfile):
        if not os.access(logfile, os.F_OK):
            return ""
        #
        f = open(logfile, "r")
        data = f.read()
        f.close()
        #
        msg = ""
        t_list = data.split("\n")
        for line in t_list:
            if not line:
                continue
            #
            if line == "Finished!":
                continue
            #
            if msg:
                msg += "\n"
            #
            msg += line
        #
        return msg

    def _processLogMessage(self, pickleFile, logfileList, defaultErrMsg):
        errMsg = ""
        for logfile in logfileList:
            err = self._getLogMessage(logfile)
            if err == "":
                continue
            #
            if errMsg != "":
                errMsg += "\n"
            #
            errMsg += err
        #
        if (errMsg == "") and (defaultErrMsg != ""):
            errMsg = defaultErrMsg
        #
        if errMsg != "":
            self._dumpPickle(pickleFile, errMsg)
            return False
        #
        return True

    def __getSession(self):
        """ Join existing session or create new session as required.
        """
        #
        self._sObj = self._reqObj.newSessionObj()
        self._sessionId = self._sObj.getId()
        self._sessionPath = self._sObj.getPath()
        if (self._verbose):
            self._lfh.write("------------------------------------------------------\n")
            self._lfh.write("+BaseClass._getSession() - creating/joining session %s\n" % self._sessionId)
            self._lfh.write("+BaseClass._getSession() - session path %s\n" % self._sessionPath)
        #

    def __loadGroupTaskPickle(self):
        """
        """
        if (self._groupTaskPickleFile is None) or (not os.access(self._groupTaskPickleFile, os.F_OK)):
            return {}
        #
        fb = open(self._groupTaskPickleFile, "rb")
        pickleData = pickle.load(fb)
        fb.close()
        return pickleData

    def __dumpGroupTaskPickle(self, pickleData):
        """
        """
        if self._groupTaskPickleFile is None:
            return
        #
        if len(pickleData) == 0:
            self._removeFile(self._groupTaskPickleFile)
            return
        #
        fb = open(self._groupTaskPickleFile, "wb")
        pickle.dump(pickleData, fb)
        fb.close()
