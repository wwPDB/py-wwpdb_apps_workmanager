##
# File:  StatusUpdater.py
# Date:  25-Apr-2017
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
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import multiprocessing, os, sys

from wwpdb.apps.workmanager.db_access.ContentDbApi import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatusDbApi  import StatusDbApi
from wwpdb.apps.workmanager.task_access.BaseClass  import BaseClass
from wwpdb.utils.rcsb.mmCIFUtil                    import mmCIFUtil
from wwpdb.utils.rcsb.MultiProcUtil                import MultiProcUtil
#

class StatusUpdater(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False,log=sys.stderr):
        """
        """
        super(StatusUpdater, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__statusTokens = ( 'status_code', 'author_approval_type', 'author_release_status_code',  'date_hold_coordinates', 'pdbx_annotator', 'process_site' )
        self.__depositionTableMap = { 'status_code':'status_code', 'author_release_status_code':'author_release_status_code', \
                                      'pdbx_annotator':'annotator_initials', 'process_site':'process_site' }
        self.__rcsb_statusTableMap = { 'status_code':'status_code', 'author_approval_type':'author_approval_type', \
                                       'author_release_status_code':'author_release_status_code', 'date_hold_coordinates':'date_hold_coordinates', \
                                       'pdbx_annotator':'rcsb_annotator', 'process_site':'process_site' }
        self.__statusInfo = {}
        self.__depositionInfo = {}
        self.__rcsb_statusInfo = {}
        self.__getStatusInfo()
        self.__writeStatusInfoCif()

    def run(self):
        """
        """
        if not os.access(os.path.join(self._sessionPath, 'statusInfo_StatusUpdater.cif'), os.F_OK):
            return 'No status info. selected.'
        #
        numProc = multiprocessing.cpu_count() / 2
        mpu = MultiProcUtil(verbose = True, log = self._lfh)
        mpu.set(workerObj = self, workerMethod = "runMulti")
        mpu.setWorkingDir(self._sessionPath)
        ok,failList,retLists,diagList = mpu.runMulti(dataList = self.__entryList, numProc = numProc, numResults = 1)
        return self.__getReturnMessage()

    def runMulti(self, dataList, procName, optionsD, workingDir):
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runSingle(entry_id)
            rList.append(entry_id)
        #
        return rList,rList,[]

    def __getStatusInfo(self):
        for token in self.__statusTokens:
            value = self._reqObj.getValue(token)
            if not value:
                continue
            #
            self.__statusInfo[token] = value
            if token in self.__depositionTableMap:
                self.__depositionInfo[self.__depositionTableMap[token]] = value
            #
            if token in self.__rcsb_statusTableMap:
                self.__rcsb_statusInfo[self.__rcsb_statusTableMap[token]] = value
            #
        #

    def __writeStatusInfoCif(self):
        self._removeFile(os.path.join(self._sessionPath, 'statusInfo_StatusUpdater.cif'))
        if not self.__statusInfo:
            return
        #
        cifUtil = mmCIFUtil()
        cifUtil.AddBlock("STATUS")
        cifUtil.AddCategory('pdbx_database_status', self.__statusTokens)
        for key,value in self.__statusInfo.items():
            cifUtil.UpdateSingleRowValue('pdbx_database_status', key, 0, value)
        #
        cifUtil.WriteCif(os.path.join(self._sessionPath, 'statusInfo_StatusUpdater.cif'))

    def __runSingle(self, entry_id):
        all_message = ''
        message,modelFile = self._getExistingArchiveFile(entry_id, 'model', 'pdbx', 'latest')
        if message:
            self._dumpPickle(entry_id + "_StatusUpdater", message)
            return
        #
        message,updatedModelFile = self.__updateModelFile(entry_id, modelFile)
        if message:
            self._dumpPickle(entry_id + "_StatusUpdater", message)
            return
        #
        archiveModelFile = self._findArchiveFileName(entry_id, 'model', 'pdbx', 'next')
        message = self._copyFileUtil(updatedModelFile, archiveModelFile)
        if message:
            self._dumpPickle(entry_id + "_StatusUpdater", message)
        else:
            self._dumpPickle(entry_id + "_StatusUpdater", 'OK')
        #

    def __updateModelFile(self, entry_id, inputFile):
        updatedModelFile = entry_id + "_StatusUpdater.cif"
        self._removeFile(os.path.join(self._sessionPath, updatedModelFile))
        logFile = 'StatusUpdater_update_cif_' + entry_id + '.log'
        clogFile = 'StatusUpdater_update_cif_command_' + entry_id + '.log'
        cmd = self._getCmd('${BINPATH}/UpdateCifCategory', inputFile, updatedModelFile, logFile, clogFile, ' -data statusInfo_StatusUpdater.cif ')
        self._runCmd(cmd)
        if os.access(os.path.join(self._sessionPath, updatedModelFile), os.F_OK):
            return '',os.path.join(self._sessionPath, updatedModelFile)
        #
        return "Status update failed.",""

    def __getReturnMessage(self):
        message = ''
        updatedList = []
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + "_StatusUpdater")
            if pickleData and pickleData != 'OK':
                message += "Status update for " + entry_id + " failed:\n\t" + pickleData + "\n"
            else:
                message += "Status update for " + entry_id + " successfully.\n"
                updatedList.append(entry_id)
            #
            self._removePickle(entry_id + "_StatusUpdater")
        #
        if updatedList:
            if self.__depositionInfo:
                statusDB = StatusDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
                for entry_id in updatedList:
                     statusDB.runUpdate(table = 'deposition', where = { 'dep_set_id' : entry_id }, data = self.__depositionInfo)
                #
            #
            if self.__rcsb_statusInfo:
                contentDB = ContentDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
                for entry_id in updatedList:
                     contentDB.runUpdate(table = 'rcsb_status', where = { 'Structure_ID' : entry_id }, data = self.__rcsb_statusInfo)
                #
            #
        #
        return message

if __name__ == '__main__':
    from wwpdb.utils.rcsb.WebRequest import InputRequest
    from wwpdb.api.facade.ConfigInfo import ConfigInfo
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose = True, log = sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002030")
    myReqObj.setValue("sessionid", "88626e0cc0b1a1bbd10bb2df8a0d68573fcbd5fe")
    myReqObj.setValue("status_code", "HPUB")
    myReqObj.setValue("author_release_status_code", "REL")
    myReqObj.setValue("date_hold_coordinates", "2017-04-25")
    myReqObj.setValue("pdbx_annotator", "LD")
    myReqObj.setValue("author_approval_type", "implicit")
    entryList = [ 'D_8000210285', 'D_8000210286' ]
    pfGenUtil = StatusUpdater(reqObj=myReqObj, entryList=entryList, verbose=False,log=sys.stderr)
    print pfGenUtil.run()
