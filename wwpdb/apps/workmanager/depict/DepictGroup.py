##
# File:  DepictGroup.py
# Date:  27-Jun-2016
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


import sys

from wwpdb.apps.workmanager.depict.DepictBase import DepictBase
from wwpdb.apps.workmanager.workflow_access.WorkflowXMLLoader import WorkflowXMLLoader


class DepictGroup(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, workFlow=False, verbose=False, log=sys.stderr):
        """
        """
        super(DepictGroup, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #
        self.__workFlowFlag = workFlow
        self.__wfTaskList = []
        self.__entryList = []
        self.__colorCodeMap = {'WF': 'groupTaskWF', 'Bucket': 'groupTaskBucket', 'UI': 'groupTaskUI'}
        self.__setup()
        self.__get_workflow_info()
        self.__get_entry_info()

    def __setup(self):
        """
        """
        self._connectStatusDB()
        self._getUserInfoDict()
        #
        if self.__workFlowFlag:
            self.__wfTaskList.append({'name' : 'run Annotation WF', 'classID' : 'runWF_Annotate_WF', 'groupclass' : self.__colorCodeMap['WF']})
            self.__wfTaskList.append({'name' : 'restart Annotation WF', 'classID' : 'restartGoWF_Annotate_WF', 'groupclass' : self.__colorCodeMap['WF']})
            self.__classInfo = self._statusDB.getWfClassByID(classID='Annotate')
            wfloader = WorkflowXMLLoader(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
            wfloader.loadWorkFlowXMLFile(self.__classInfo['class_file'])
            wfWorkFlowInfo = wfloader.getWorkFlowInfo()
            for wfType in ('WF', 'Bucket'):
                for wf in wfWorkFlowInfo.values():
                    if 'classID' not in wf:
                        continue
                    #
                    myD = {}
                    myD['name'] = 'restart ' + wf['name'] + ' ' + wfType
                    myD['classID'] = 'restartGoWF_' + wf['classID'] + '_' + wfType
                    myD['groupclass'] = self.__colorCodeMap[wfType]
                    self.__wfTaskList.append(myD)
                #
            #
        #
        entryIdList = self._statusDB.getEntryListForGroup(groupids=[self._reqObj.getValue("identifier")])
        if entryIdList:
            for entry in entryIdList:
                if self.__workFlowFlag:
                    for item in ('sessionid', 'annotator'):
                        entry[item] = self._reqObj.getValue(item)
                    #
                #
                self.__entryList.append(entry)
            #
        #

    def __get_workflow_info(self):
        """
        """
        if not self.__wfTaskList:
            return
        #
        MaxTask = 5
        module_tmplt = self._getPageTemplate('module_tmplt')
        count = 0
        workflow_info = '<tr>\n'
        for wfTask in self.__wfTaskList:
            if count == MaxTask:
                count = 0
                workflow_info += '</tr>\n<tr>\n'
            #
            workflow_info += module_tmplt % wfTask
            count += 1
        #
        workflow_info += '</tr>\n<tr>\n'
        for wfMod in ('TransMod', 'LigMod', 'SeqMod', 'AnnMod', 'ValMod'):
            myD = {}
            myD['name'] = 'restart ' + wfMod + ' UI'
            myD['classID'] = 'restartGoWF_' + wfMod + '_UI'
            myD['groupclass'] = self.__colorCodeMap['UI']
            workflow_info += module_tmplt % myD
        #
        workflow_info += '</tr>\n'
        self._dataInfo['workflow_info'] = workflow_info

    def __get_entry_info(self):
        """
        """
        if self.__workFlowFlag:
            MaxEntry = 6
            entry_tmplt = self._getPageTemplate('entry_tmplt')
        else:
            MaxEntry = 2
            entry_tmplt = self._getPageTemplate('task_entry_tmplt')
        #
        count = 0
        entry_info = '<tr>\n'
        for entry in self.__entryList:
            if count == MaxEntry:
                count = 0
                entry_info += '</tr>\n<tr>\n'
            #
            entry_info += entry_tmplt % entry
            count += 1
        #
        entry_info += '</tr>\n'
        self._dataInfo['entry_info'] = entry_info
