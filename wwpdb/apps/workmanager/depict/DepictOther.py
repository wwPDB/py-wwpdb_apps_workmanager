##
# File:  DepictOther.py
# Date:  25-Mar-2016
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


import os, sys, urllib

from wwpdb.api.status.dbapi.WFEtime                 import getTimeFromEpoc
from wwpdb.apps.ann_tasks_v2.filer.FileUtils        import FileUtils
from wwpdb.apps.workmanager.depict.DepictBase       import DepictBase,processPublicIDs
from wwpdb.apps.workmanager.depict.DepictWorkFlow   import DepictWorkFlow
from wwpdb.apps.workmanager.file_access.LogFileUtil import LogFileUtil

class DepictOther(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(DepictOther, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #
        self.__dataD = {}
        self.__lastInst = {}
        self.__setup()

    def SummaryPage(self):
        """
        """
        self._dataInfo['summary_tmplt'] = [ self.__dataD ]
        #
        self._connectContentDB()
        c_authors = self._contentDB.ContactAuthor(depositionid=self._reqObj.getValue("identifier"))
        if c_authors:
            self._dataInfo['contact_table_row_tmplt'] = list(c_authors)
        #
        audit_history  = self._contentDB.AuditHistory(depositionid=self._reqObj.getValue("identifier"))
        if audit_history:
            hisList = []
            for Dict in audit_history:
                myD = {}
                for item in ( 'public_version', 'date', 'file_version' ):
                    myD[item] = ''
                #
                if ('major_revision' in Dict) and ('minor_revision' in Dict):
                    myD['public_version'] = str(Dict['major_revision']) + '.' + str(Dict['minor_revision'])
                #
                if ('revision_date' in Dict) and Dict['revision_date']:
                    myD['date'] = Dict['revision_date'].strftime("%b. %d, %Y")
                #
                if ('internal_version' in Dict) and Dict['internal_version']:
                    myD['file_version'] = 'V' + str(Dict['internal_version'])
                #
                hisList.append(myD)
            #
            self._dataInfo['audit_history_table_row_tmplt'] = hisList
        #
        timestamps = self._statusDB.getTimeStampInfo(depositionid=self._reqObj.getValue("identifier"))
        if timestamps:
            self._dataInfo['timestamp_table_row_tmplt'] = list(timestamps)
            for dir in self._dataInfo['timestamp_table_row_tmplt']:
                if ('mtime' in dir) and dir['mtime']:
                    dir['mtime'] = getTimeFromEpoc(dir['mtime'])
                #
            #
        #

    def AllFilePage(self):
        """
        """
        fu = FileUtils(self._reqObj.getValue("identifier"), reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        for item in ( 'archive', 'deposit', 'wf_instance' ):
            nFiles, list = fu.renderFileList(fileSource=item)
            self.__dataD[item] = '\n'.join(list)
        #
        self._dataInfo['allfile_tmplt'] = [ self.__dataD ]

    def getLevelPageSetting(self, page_tmplt):
        """
        """
        self.__getLastInst()
        method = self.__getInstanceData('dep_exp_method')
        if method:
            self._reqObj.setValue('method', method)
            self._reqObj.setValue("urlmethod", urllib.quote(method))
        #
        if page_tmplt == 'level3_tmplt':
            self.__depictLevel3WorkFlow()
        #
        self._dataInfo[page_tmplt] = [ self.__dataD ]
        self._dataInfo['entry_tmplt'] = [ self.__lastInst ]

    def DepictLevel2WorkFlow(self):
        """
        """
        self._reqObj.setValue("classID", "Annotate")
        for item in ( 'wf_inst_id', 'wf_class_id' ):
            self._reqObj.setValue(item, self.__getInstanceData(item))
            #
        #
        depictWF = DepictWorkFlow(reqObj=self._reqObj, statusDB=self._statusDB, conFigObj=self._conFigObj, verbose=self._verbose, log=self._lfh)
        depictWF.getLevel2Setting()
        return depictWF.getPageText(page_id='workflow_tmplt')

    def __setup(self):
        """
        """
        self._connectStatusDB()
        self._getUserInfoDict()
        #
        self.__dataD = processPublicIDs(self._statusDB.getDepInfo(depositionid=self._reqObj.getValue("identifier")))

    def __getLastInst(self):
        """
        """
        self.__lastInst = processPublicIDs(self._statusDB.getLastInstance(depositionid=self._reqObj.getValue("identifier")))

    def __getInstanceData(self, item):
        """
        """
        val = ''
        if self.__lastInst and (item in self.__lastInst) and self.__lastInst[item]:
            val = str(self.__lastInst[item])
        #
        return val

    def __depictLevel3WorkFlow(self):
        """
        """
        logUtil = LogFileUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        logFilePath = logUtil.getLogFile()
        if logFilePath:
            myD = {}
            for item in ( 'identifier', 'sessionid', 'instance', 'classID' ):
                myD[item] = self._reqObj.getValue(item)
            #
            log_tmplt = self._getPageTemplate('download_wf_log_tmplt')
            self.__dataD['log_file'] = log_tmplt % myD
        #
        depictWF = DepictWorkFlow(reqObj=self._reqObj, statusDB=self._statusDB, conFigObj=self._conFigObj, verbose=self._verbose, log=self._lfh)
        wfD = depictWF.getLevel3Setting()
        self.__dataD.update(wfD)
