##
# File:  CopyFileToAutoGroup.py
# Date:  29-Jun-2016
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

import multiprocessing
import os
import shutil
import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.io.locator.DataReference import DataFileReference
from rcsb.utils.multiproc.MultiProcUtil import MultiProcUtil
from wwpdb.io.locator.PathInfo import PathInfo
#


class CopyFileToAutoGroup(object):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__entryList = entryList
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = str(self.__reqObj.getValue('WWPDB_SITE_ID'))
        self.__cI = ConfigInfo(self.__siteId)
        self.__cICommon = ConfigInfoAppCommon(self.__siteId)
        self.__archivePath = self.__cI.get('SITE_ARCHIVE_STORAGE_PATH')
        self.__identifier = str(self.__reqObj.getValue('identifier'))
        self.__targetPath = os.path.join(self.__archivePath, 'autogroup', self.__identifier, 'processed')
        #
        self.__rcsbRoot = self.__cICommon.get_site_annot_tools_path()
        self.__compRoot = self.__cICommon.get_site_cc_cvs_path()
        self.__dictBinRoot = os.path.join(self.__cICommon.get_site_packages_path(), 'dict', 'bin')
        self.__dictRoot = self.__cICommon.get_mmcif_dict_path()
        self.__dictionary_v40 = self.__cI.get('SITE_PDBX_V4_DICT_NAME') + '.sdb'
        self.__dictionary_v5 = self.__cICommon.get_mmcif_archive_next_dict_filename() + '.sdb'
        #
        # self.__sessionId = None
        self.__sessionPath = None
        #
        self.__dfRef = DataFileReference(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        self.__dfRef.setStorageType('session')
        self.__dfRef.setPartitionNumber("1")
        self.__dfRef.setVersionId("none")
        #
        self.__getSession()
        self.__pI = PathInfo(siteId=self.__siteId, sessionPath=self.__sessionPath, verbose=self.__verbose, log=self.__lfh)
        #
        self.__fileTypeList = [ [ 'model',                  'pdbx' ],  # noqa: E201,E202,E241
                                [ 'structure-factors',      'pdbx' ],  # noqa: E201,E202,E241
                                [ 'validation-report-full', 'pdf'  ],  # noqa: E201,E202,E241
                                [ 'validation-report',      'pdf'  ],  # noqa: E201,E202,E241
                                [ 'validation-data',        'xml'  ] ]  # noqa: E201,E202,E241
        #

    def run(self):
        """
        """
        numProc = int(multiprocessing.cpu_count() / 2)
        mpu = MultiProcUtil(verbose=True)
        mpu.set(workerObj=self, workerMethod="runMulti")
        mpu.setWorkingDir(self.__sessionPath)
        _ok, _failList, _retLists, _diagList = mpu.runMulti(dataList=self.__entryList, numProc=numProc, numResults=1)
        return self.__getReturnMessage()

    def runMulti(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            processedPath = os.path.join(self.__targetPath, entry_id)
            if not os.path.isdir(processedPath):
                os.mkdir(processedPath)
            #
            self.__dfRef.setSessionPath(processedPath)
            self.__dfRef.setSessionDataSetId(entry_id)
            for fileType in self.__fileTypeList:
                sourceFile = self.__pI.getFilePath(dataSetId=entry_id, wfInstanceId=None, contentType=fileType[0], formatType=fileType[1],
                                                   fileSource='archive', versionId='latest', partNumber='1')
                if (not sourceFile) or (not os.access(sourceFile, os.F_OK)):
                    continue
                #
                self.__dfRef.setContentTypeAndFormat(fileType[0], fileType[1])
                targetFile = self.__dfRef.getFilePathReference()
                if fileType[0] == 'model' and fileType[1] == 'pdbx':
                    self.__generateV4PdbxFile(sourceFile, entry_id + '.cif', entry_id + '.cif_log')
                    cifFile = os.path.join(self.__sessionPath, entry_id + '.cif')
                    if os.access(cifFile, os.F_OK):
                        shutil.copyfile(cifFile, targetFile)
                    #
                    self.__generatePdbFile(sourceFile, entry_id + '.pdb', entry_id + '.log', entry_id + '.pdb_log')
                    pdbFile = os.path.join(self.__sessionPath, entry_id + '.pdb')
                    if os.access(pdbFile, os.F_OK):
                        self.__dfRef.setContentTypeAndFormat(fileType[0], 'pdb')
                        targetPdbFile = self.__dfRef.getFilePathReference()
                        shutil.copyfile(pdbFile, targetPdbFile)
                    #
                else:
                    shutil.copyfile(sourceFile, targetFile)
                #
            #
            rList.append(entry_id)
        #
        return rList, rList, []

    def __getSession(self):
        """
        """
        self.__sObj = self.__reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()

    def __generateV4PdbxFile(self, inputFile, outputFileName, commandLogFile):
        """
        """
        cmd = 'cd ' + self.__sessionPath + ' ; ' + self.__dictBinRoot + '/cifexch2 -dicSdb ' + os.path.join(self.__dictRoot, self.__dictionary_v5) \
            + ' -pdbxDicSdb ' + os.path.join(self.__dictRoot, self.__dictionary_v40) + ' -reorder -strip -op in -pdbids -input ' \
            + inputFile + ' -output ' + outputFileName + ' > ' + commandLogFile + ' 2>&1 ; '
        os.system(cmd)

    def __generatePdbFile(self, inputFile, outputFileName, outputLogFile, commandLogFile):
        """
        """
        cmd = 'cd ' + self.__sessionPath + ' ; RCSBROOT=' + self.__rcsbRoot + ' ; export RCSBROOT ; COMP_PATH=' + self.__compRoot \
            + ' ; export COMP_PATH ; BINPATH=${RCSBROOT}/bin; export BINPATH; ${BINPATH}/maxit -i ' + inputFile + ' -o 2 -output ' \
            + outputFileName + ' -log ' + outputLogFile + ' > ' + commandLogFile + ' 2>&1 ; '
        os.system(cmd)

    def __getReturnMessage(self):
        """
        """
        message = ''
        for entry_id in self.__entryList:
            processedPath = os.path.join(self.__targetPath, entry_id)
            self.__dfRef.setSessionPath(processedPath)
            self.__dfRef.setSessionDataSetId(entry_id)
            found = False
            for fileType in self.__fileTypeList:
                sourceFile = self.__pI.getFilePath(dataSetId=entry_id, wfInstanceId=None, contentType=fileType[0], formatType=fileType[1],
                                                   fileSource='archive', versionId='latest', partNumber='1')
                if (not sourceFile) or (not os.access(sourceFile, os.F_OK)):
                    continue
                #
                self.__dfRef.setContentTypeAndFormat(fileType[0], fileType[1])
                targetFile = self.__dfRef.getFilePathReference()
                if os.access(targetFile, os.F_OK):
                    found = True
                else:
                    message += 'Missing ' + targetFile + '\n'
                #
                if fileType[0] == 'model' and fileType[1] == 'pdbx':
                    self.__dfRef.setContentTypeAndFormat(fileType[0], 'pdb')
                    targetPdbFile = self.__dfRef.getFilePathReference()
                    if os.access(targetPdbFile, os.F_OK):
                        found = True
                    else:
                        message += 'Missing ' + targetPdbFile + '\n'
                    #
                #
            #
            if found:
                message += 'Copied entry ' + entry_id + '\n'
            #
        #
        return message


def main_copy():
    from wwpdb.utils.session.WebRequest import InputRequest
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002003")
    myReqObj.setValue("sessionid", " b8030220bdf3559c10a2c63618cd85a25256f7c1")
    entryList = ['D_8000200001', 'D_8000200003', 'D_8000200027', 'D_8000200040']
    copyUtil = CopyFileToAutoGroup(reqObj=myReqObj, entryList=entryList, verbose=False, log=sys.stderr)
    copyUtil.run()


if __name__ == '__main__':
    main_copy()
