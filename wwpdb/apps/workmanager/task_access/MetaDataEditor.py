##
# File:  MetaDataEditor.py
# Date:  23-Feb-2018
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2018 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"

import copy
import json
import multiprocessing
import os
import sys

from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
#


class MetaDataEditor(BaseClass):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(MetaDataEditor, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__task = str(self._reqObj.getValue("task"))
        self.__dataType = str(self._reqObj.getValue("data_type"))
        #
        self.__statusCode = "ok"
        self.__errorMessage = ""
        self.__processMessage = ""
        self.__pickleFile = "metaData"
        self.__pickleObj = {}

    def setLogHandle(self, log=sys.stderr):
        """  Reset the stream for logging output.
        """
        try:
            self._lfh = log
            return True
        except:  # noqa: E722 pylint: disable=bare-except
            return False
        #

    def ProcessForm(self):
        """
        """
        try:
            getattr(self, "%s" % self.__task)()
        except:  # noqa: E722 pylint: disable=bare-except
            if self.__errorMessage:
                self.__errorMessage += "\n"
            #
            self.__errorMessage += "Running process '" + self.__task + "' failed."
        #
        self.__pickleObj["statuscode"] = self.__statusCode
        self.__pickleObj["selected_datatype"] = self.__dataType
        for msgType in ("error", "message"):
            if msgType in self.__pickleObj:
                del self.__pickleObj[msgType]
            #
        #
        if self.__errorMessage:
            self.__pickleObj["error"] = self.__errorMessage
        #
        if self.__processMessage:
            self.__pickleObj["message"] = self.__processMessage
        #
        self._dumpPickle(self.__pickleFile, self.__pickleObj)
        #
        return True

    def GetFormProcessingResult(self):
        """
        """
        self.__pickleObj = self._loadPickle(self.__pickleFile)
        if ("statuscode" in self.__pickleObj) and self.__pickleObj["statuscode"]:
            self.__statusCode = self.__pickleObj["statuscode"]
        #
        if ("error" in self.__pickleObj) and self.__pickleObj["error"]:
            self.__errorMessage = self.__pickleObj["error"]
        #
        myD = {}
        myD["statuscode"] = self.__statusCode
        myD["statustext"] = self.__errorMessage
        if (self.__task == "get_entry") or (self.__task == "get_value"):
            self.__dataType = ""
            if ("selected_datatype" in self.__pickleObj) and self.__pickleObj["selected_datatype"]:
                self.__dataType = self.__pickleObj["selected_datatype"]
            #
            entryList = []
            if ("all_entry_ids" in self.__pickleObj) and self.__pickleObj["all_entry_ids"]:
                entryList = self.__pickleObj["all_entry_ids"]
            #
            htmlcontent = ""
            for entry_id in entryList:
                htmlcontent += self.__depictEntry(entry_id)
            #
            if htmlcontent:
                myD["htmlcontent"] = htmlcontent
            else:
                myD["statuscode"] = "failed"
                if not myD["statustext"]:
                    myD["statustext"] = "Load data failed."
                #
            #
        elif ("message" in self.__pickleObj) and self.__pickleObj["message"]:
            if myD["statustext"]:
                myD["statustext"] += "\n\n"
            #
            myD["statustext"] += self.__pickleObj["message"]
        #
        return myD

    def get_entry(self):
        """
        """
        self._removePickle(self.__pickleFile)
        #
        entry_ids = str(self._reqObj.getValue("entry_ids"))
        if not entry_ids:
            self.__errorMessage = "No Entry IDs defined."
            self.__statusCode = "failed"
            return
        #
        statusDB = StatusDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        self.__errorMessage, selectedEntryList = statusDB.getEntryIdListFromInputIdString(entry_ids)
        if not selectedEntryList:
            self.__statusCode = "failed"
            return
        #
        self.__all_data_type = str(self._reqObj.getValue("all_data_type"))  # pylint: disable=attribute-defined-outside-init
        all_data_type = self.__all_data_type.split(",")
        #
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod="runGetEntriesInfo")
        mpu.setWorkingDir(self._sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=selectedEntryList, numProc=numProc, numResults=1)
        #
        validEntryList = []
        for entry_id in selectedEntryList:
            entryPickle = self._loadPickle(entry_id + "_MetaDataEditor")
            if ("error" in entryPickle) and entryPickle["error"]:
                if self.__errorMessage:
                    self.__errorMessage += "\n"
                #
                self.__errorMessage += entryPickle["error"]
            elif ("file" in entryPickle) and entryPickle["file"] and ("info" in entryPickle) and entryPickle["info"]:
                infoD = {}
                infoD["file"] = entryPickle["file"]
                if ("pdbid" in entryPickle["info"]) and entryPickle["info"]["pdbid"]:
                    infoD["pdbid"] = entryPickle["info"]["pdbid"]
                #
                if ("_pdbx_database_status.status_code" in entryPickle["info"]) and entryPickle["info"]["_pdbx_database_status.status_code"]:
                    infoD["status_code"] = entryPickle["info"]["_pdbx_database_status.status_code"]
                #
                if ("_pdbx_database_status.pdbx_annotator" in entryPickle["info"]) and entryPickle["info"]["_pdbx_database_status.pdbx_annotator"]:
                    infoD["annotator"] = entryPickle["info"]["_pdbx_database_status.pdbx_annotator"]
                #
                dataD = {}
                for data_type in all_data_type:
                    if (data_type in entryPickle["info"]) and entryPickle["info"][data_type]:
                        dataD[data_type] = entryPickle["info"][data_type]
                    #
                #
                infoD["original_data"] = dataD
                infoD["current_data"] = copy.deepcopy(dataD)
                self.__pickleObj[entry_id] = infoD
                validEntryList.append(entry_id)
            #
            self._removePickle(entry_id + "_MetaDataEditor")
        #
        if not validEntryList:
            self.__statusCode = "failed"
        else:
            self.__pickleObj["all_entry_ids"] = validEntryList
        #

    def get_value(self):
        """
        """
        self.__pickleObj = self._loadPickle(self.__pickleFile)

    def save_value(self):
        """
        """
        self.__pickleObj = self._loadPickle(self.__pickleFile)
        entryList = self.__getEntryList()
        if not entryList:
            return
        #
        for entry_id in entryList:
            value = str(self._reqObj.getValue("current_" + entry_id))
            # updated = False
            if (entry_id in self.__pickleObj) and self.__pickleObj[entry_id] and ("current_data" in self.__pickleObj[entry_id]) and \
               self.__pickleObj[entry_id]["current_data"]:
                self.__pickleObj[entry_id]["current_data"][self.__dataType] = value
                if self.__processMessage:
                    self.__processMessage += "\n"
                #
                self.__processMessage += "Value saved for " + entry_id + "."
            else:
                if self.__errorMessage:
                    self.__errorMessage += "\n"
                #
                self.__errorMessage += "Saving value failed for " + entry_id + "."
            #
        #

    def update_file(self):
        """
        """
        self.__pickleObj = self._loadPickle(self.__pickleFile)
        entryList = self.__getEntryList()
        if not entryList:
            return
        #
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod="runUpdateEntriesInfo")
        mpu.setWorkingDir(self._sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=entryList, numProc=numProc, numResults=1)
        #
        for entry_id in entryList:
            entryPickle = self._loadPickle(entry_id + "_MetaDataEditor")
            if ("error" in entryPickle) and entryPickle["error"]:
                if self.__errorMessage:
                    self.__errorMessage += "\n"
                #
                self.__errorMessage += entryPickle["error"]
            elif ("message" in entryPickle) and entryPickle["message"]:
                if self.__processMessage:
                    self.__processMessage += "\n"
                #
                self.__processMessage += entryPickle["message"]
            #
            self._removePickle(entry_id + "_MetaDataEditor")
        #

    def runGetEntriesInfo(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runGetEntryInfo(entry_id)
            rList.append(entry_id)
        #
        return rList, rList, []

    def runUpdateEntriesInfo(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runUpdateEntryInfo(entry_id)
            rList.append(entry_id)
        #
        return rList, rList, []

    def __runGetEntryInfo(self, entry_id):
        """
        """
        entryPickle = {}
        message, modelFile = self._getExistingArchiveFile(entry_id, "model", "pdbx", "latest")
        if message:
            entryPickle["error"] = message
            self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)
            return
        #
        entryPickle["file"] = modelFile
        message, info = self.__getEntryInfoFromModelFile(entry_id, modelFile)
        if message:
            entryPickle["error"] = message
            self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)
            return
        #
        entryPickle["info"] = info
        self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)

    def __getEntryInfoFromModelFile(self, entry_id, inputFile):
        """
        """
        jsonFile = entry_id + "_MetaDataEditor.json"
        logFile = "MetaDataEditor_" + entry_id + ".log"
        clogFile = "MetaDataEditor_command_" + entry_id + ".log"
        extraOption = " -data_type '" + self.__all_data_type + ",_pdbx_database_status.status_code,_pdbx_database_status.pdbx_annotator,pdbid' "
        cmd = self._getCmd("${BINPATH}/GetMetaDataInfo", inputFile, jsonFile, logFile, clogFile, extraOption)
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
            return msg, {}
        #
        if os.access(os.path.join(self._sessionPath, jsonFile), os.F_OK):
            with open(os.path.join(self._sessionPath, jsonFile), "r") as f:
                jsonObj = json.load(f)
            #
            return "", jsonObj
        #
        return "Get entry information failed.", {}

    def __depictEntry(self, entry_id):
        """
        """
        if not self.__dataType:
            return ""
        #
        myD = {}
        myD["entry_id"] = entry_id
        for item in ("original_data", "current_data", "pdbid", "status_code", "annotator"):
            myD[item] = ""
        #
        if (entry_id in self.__pickleObj) and self.__pickleObj[entry_id]:
            for item in ("pdbid", "status_code", "annotator"):
                if (item in self.__pickleObj[entry_id]) and self.__pickleObj[entry_id][item]:
                    myD[item] = self.__pickleObj[entry_id][item]
                #
            #
            for item in ("original_data", "current_data"):
                if (item not in self.__pickleObj[entry_id]) or (not self.__pickleObj[entry_id][item]):
                    continue
                #
                if (self.__dataType not in self.__pickleObj[entry_id][item]) or (not self.__pickleObj[entry_id][item][self.__dataType]):
                    continue
                #
                value = self.__pickleObj[entry_id][item][self.__dataType]
                if item == "original_data":
                    value = value.replace('"', '\\"')
                #
                myD[item] = value
            #
        #
        return self._processTemplate("editing_entry_tmplt.html", myD)

    def __getEntryList(self):
        """
        """
        entryList = self._reqObj.getValueList('entry')
        if not entryList:
            self.__statusCode = "failed"
            self.__errorMessage = "No Entry selected."
        #
        return entryList

    def __runUpdateEntryInfo(self, entry_id):
        """
        """
        entryPickle = {}
        #
        if (entry_id not in self.__pickleObj) or (not self.__pickleObj[entry_id]) or ("current_data" not in self.__pickleObj[entry_id]) or \
           (not self.__pickleObj[entry_id]["current_data"]) or ("file" not in self.__pickleObj[entry_id]) or (not self.__pickleObj[entry_id]["file"]):
            entryPickle["error"] = "Updating " + entry_id + " failed."
            self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)
            return
        #
        dataFile = self.__writeDataCifFile(entry_id, self.__pickleObj[entry_id]["current_data"])
        #
        message, updatedModelFile = self.__updateModelFile(entry_id, self.__pickleObj[entry_id]["file"], dataFile)
        if message:
            entryPickle["error"] = "Updating " + entry_id + " failed:\n" + message
            self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)
            return
        #
        archiveModelFile = self._findArchiveFileName(entry_id, 'model', 'pdbx', 'next')
        message = self._copyFileUtil(updatedModelFile, archiveModelFile)
        if message:
            entryPickle["error"] = "Updating " + entry_id + " failed:\n" + message
        else:
            entryPickle["message"] = entry_id + " updated."
        #
        self._dumpPickle(entry_id + "_MetaDataEditor", entryPickle)

    def __writeDataCifFile(self, entry_id, dataInfo):
        """
        """
        dataFile = entry_id + "_data.cif"
        cifObj = mmCIFUtil()
        cifObj.AddBlock(entry_id)
        categoryMap = {}
        for key, v in dataInfo.items():
            value = v
            if not value:
                value = "?"
            #
            cList = key.split(".")
            if cList[0][1:] in categoryMap:
                categoryMap[cList[0][1:]][0].append(cList[1])
                categoryMap[cList[0][1:]][1][0].append(value)
            else:
                categoryMap[cList[0][1:]] = [[cList[1]], [[value]]]
            #
        #
        for key, values in categoryMap.items():
            cifObj.AddCategory(key, values[0])
            cifObj.InsertData(key, values[1])
        #
        cifObj.WriteCif(outputFilePath=os.path.join(self._sessionPath, dataFile))
        return dataFile

    def __updateModelFile(self, entry_id, modelFile, dataFile):
        """
        """
        updatedModelFile = entry_id + "_MetaDataEditor.cif"
        # jsonFile = entry_id + "_MetaDataEditor.json"
        logFile = "MetaDataEditor_" + entry_id + ".log"
        clogFile = "MetaDataEditor_command_" + entry_id + ".log"
        extraOption = " -data_file " + dataFile + " "
        cmd = self._getCmd("${BINPATH}/MergeMetaDataInfo", modelFile, updatedModelFile, logFile, clogFile, extraOption)
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
            return msg, ''
        #
        if os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            return "", os.path.join(self._sessionPath, updatedModelFile)
        #
        return "Merge metadata information failed.", ""
