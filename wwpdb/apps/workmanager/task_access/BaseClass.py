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
import os
import shutil
import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.io.locator.PathInfo import PathInfo


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
        self._archivePath = self._cI.get('SITE_ARCHIVE_STORAGE_PATH')
        #
        self.__getSession()
        self._pI = PathInfo(siteId=self._siteId, sessionPath=self._sessionPath, verbose=self._verbose, log=self._lfh)

    def _getExistingArchiveFile(self, entryId, contentType, formatType, version):
        filePath = self._findArchiveFileName(entryId, contentType, formatType, version)
        message = ''
        if not filePath:
            message = "Can not find " + version + " " + contentType + " " + formatType + " file."
        elif not os.access(filePath, os.F_OK):
            message = "File " + filePath + " does not exist."
        #
        return message, filePath

    def _findArchiveFileName(self, entryId, contentType, formatType, version):
        return self._pI.getFilePath(dataSetId=entryId, wfInstanceId=None, contentType=contentType, formatType=formatType,
                                    fileSource='archive', versionId=version, partNumber='1')

    def _copyFileUtil(self, sourcePath, targetPath):
        if not sourcePath:
            return 'Copying file: No source file defined.'
        #
        if not targetPath:
            return 'Copying file: No target file defined.'
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
        return ''

    def _bashSetting(self):
        setting = " RCSBROOT=" + self._cICommon.get_site_annot_tools_path() + "; export RCSBROOT; " \
            + " COMP_PATH=" + self._cICommon.get_site_cc_cvs_path() + "; export COMP_PATH; " \
            + " BINPATH=${RCSBROOT}/bin; export BINPATH; " \
            + " LOCALBINPATH=" + os.path.join(self._cICommon.get_site_local_apps_path(), 'bin') + "; export LOCALBINPATH; " \
            + " DICTBINPATH=" + os.path.join(self._cICommon.get_site_packages_path(), 'dict', 'bin') + "; export DICTBINPATH; "
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
        # self._lfh.write('running cmd=%s\n' % cmd)
        os.system(cmd)

    def _removeFile(self, filePath):
        if os.access(filePath, os.F_OK):
            os.remove(filePath)
        #

    def _dumpPickle(self, pickleFile, pickleData):
        fb = open(os.path.join(self._sessionPath, pickleFile + '.pickle'), 'wb')
        pickle.dump(pickleData, fb)
        fb.close()

    def _loadPickle(self, pickleFile):
        picklePath = os.path.join(self._sessionPath, pickleFile + '.pickle')
        if not os.access(picklePath, os.F_OK):
            return None
        #
        fb = open(picklePath, 'rb')
        pickleData = pickle.load(fb)
        fb.close()
        return pickleData

    def _removePickle(self, pickleFile):
        self._removeFile(os.path.join(self._sessionPath, pickleFile + '.pickle'))

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
        ifh = open(fPath, 'r')
        sIn = ifh.read()
        ifh.close()
        return (sIn % parameterDict)

    def _getLogMessage(self, logfile):
        if not os.access(logfile, os.F_OK):
            return ''
        #
        f = open(logfile, 'r')
        data = f.read()
        f.close()
        #
        msg = ''
        t_list = data.split('\n')
        for line in t_list:
            if not line:
                continue
            #
            if line == 'Finished!':
                continue
            #
            if msg:
                msg += '\n'
            #
            msg += line
        #
        return msg

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
