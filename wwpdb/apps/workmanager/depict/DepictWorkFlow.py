##
# File:  DepictWorkFlow.py
# Date:  24-Mar-2016
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
try:
    from urllib.parse import quote as u_quote
except ImportError:
    from urllib import quote as u_quote

from wwpdb.utils.wf.dbapi.WFEtime import getTimeString
from wwpdb.apps.workmanager.depict.DepictBase import DepictBase
from wwpdb.apps.workmanager.file_access.LogFileUtil import LogFileUtil
from wwpdb.apps.workmanager.workflow_access.WorkflowXMLLoader import WorkflowXMLLoader
from wwpdb.io.locator.PathInfo import PathInfo


class DepictWorkFlow(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(DepictWorkFlow, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #
        self.__sObj = self._reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__MaxBox = 7
        self.__MaxBoxTask = 4
        #
        self.__setup()

    def __setup(self):
        """
        """
        self._connectStatusDB()
        self.__classInfo = self._statusDB.getWfClassByID(classID=self._reqObj.getValue("classID"))
        #
        wfloader = WorkflowXMLLoader(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        wfloader.loadWorkFlowXMLFile(self.__classInfo['class_file'])
        #
        self.__wfMetaDataInfo = wfloader.getMetaDataInfo()
        # self.__wfMetaDataInfo['title'] = classInfo['title']
        self.__wfWorkFlowInfo = wfloader.getWorkFlowInfo()
        self.__wfFlow = self.__wfWorkFlowInfo.values()
        #
        self.__interface_tmplt = self._getPageTemplate('interface_tmplt')

    def getLevel2Setting(self):
        """
        """
        dataD = self.__wfMetaDataInfo
        dataD['wf_entry_id'] = self.__wfFlow[0]['taskID']
        dataD['wf_entry_name'] = self.__wfFlow[0]['name']
        dataD['wf_exit_id'] = self.__wfFlow[-1]['taskID']
        dataD['wf_exit_name'] = self.__wfFlow[-1]['name']
        self._dataInfo['workflow_tmplt'] = [dataD]
        #
        self.__download_tmplt = self._getPageTemplate('download_tmplt')  # pylint: disable=attribute-defined-outside-init
        self.__depictLevel2WorkFlow()
        self.__depictRunWorkFlowInfo()

    def getLevel3Setting(self):
        """
        """
        wfD = self.__wfMetaDataInfo
        wfD['title'] = self.__classInfo['title']
        lastWFInstance = self._statusDB.getLastWFInstance(depositionid=self._reqObj.getValue('identifier'), classid=self._reqObj.getValue('classID'))
        if lastWFInstance:
            if ('inst_status' in lastWFInstance) and lastWFInstance['inst_status']:
                wfD['inst_status'] = lastWFInstance['inst_status']
            #
            if ('status_timestamp' in lastWFInstance) and lastWFInstance['status_timestamp']:
                wfD['status_timestamp'] = getTimeString(lastWFInstance['status_timestamp'])
            #
        #
        wfD['task_info'] = self.__depictLevel3TaskInfo()
        return wfD

    def __depictLevel2WorkFlow(self):
        """
        """
        workflow_module_tmplt = self._getPageTemplate('workflow_module_tmplt')
        notdone_module_tmplt = self._getPageTemplate('notdone_module_tmplt')
        single_module_tmplt = self._getPageTemplate('single_module_tmplt')
        single_module_UI_tmplt = self._getPageTemplate('single_module_UI_tmplt')
        #
        work_module = '<tr>\n'
        single_module = '<tr>\n'
        count = 0
        for wf in self.__wfFlow[1:-1]:
            if 'classID' not in wf:
                continue
            #
            if count == self.__MaxBox:
                count = 0
                work_module += '</tr>\n<tr>\n'
                single_module += '</tr>\n<tr>\n'
            #
            myD = self.__initializeMyD()
            myD = self.__expandMyD(myD, wf, ('classID', 'taskID', 'name'))
            myD['inst_status'] = 'notdone'
            myD['instance'] = ''
            lastWFInstance = self._statusDB.getLastWFInstance(depositionid=self._reqObj.getValue('identifier'), classid=wf['classID'])
            myD = self.__expandMyD(myD, lastWFInstance, ('inst_status', 'wf_inst_id'))
            if not myD['inst_status']:
                myD['inst_status'] = 'notdone'
            #
            myD['run_with_ui'] = ''
            if wf['classID'] in ('TransMod', 'LigMod', 'SeqMod' , 'AnnMod'):
                myD['run_with_ui'] = single_module_UI_tmplt % myD
            elif wf['classID'] == 'ValMod':
                groupId = self._reqObj.getValue('group_id')
                if groupId and groupId.startswith('G_'):
                    myD['run_with_ui'] = single_module_UI_tmplt % myD
                #
            #
            myD['open_interface'] = ''
            if myD['inst_status'] == 'notdone':
                work_module += notdone_module_tmplt % myD
            else:
                myD['download_ciffile'] = self.__processDownLoadCifFile(myD, ' | ')
                if myD['inst_status'] == 'waiting':
                    myD['base_url'] = self._processBaseUrl(wf['classID'])
                    myD['style'] = ''
                    myD['open_interface'] = self.__interface_tmplt % myD + '<br/>'
                #
                work_module += workflow_module_tmplt % myD
            #
            single_module += single_module_tmplt % myD
            count += 1
        #
        work_module += '</tr>\n'
        single_module += '</tr>\n'
        self._dataInfo['sub_workflow_module'] = work_module
        self._dataInfo['single_workflow_module'] = single_module

    def __depictRunWorkFlowInfo(self):
        """
        """
        wf_list = self._statusDB.getAllWFInstances(depositionid=self._reqObj.getValue('identifier'))
        if not wf_list:
            return
        #
        run_module_tmplt = self._getPageTemplate('run_module_tmplt')
        #
        contents = '<tr>\n'
        count = 0
        hasValue = False
        for dir in wf_list:  # pylint: disable=redefined-builtin
            if ('inst_status' in dir) and dir['inst_status'] == 'aborted':
                continue
            #
            hasValue = True
            if count == self.__MaxBox:
                count = 0
                contents += '</tr>\n<tr>\n'
            #
            myD = self.__initializeMyD()
            myD = self.__expandMyD(myD, dir, ('inst_status', 'wf_inst_id', 'wf_class_id', 'status_timestamp'))
            myD['download_ciffile'] = self.__processDownLoadCifFile(myD, '')
            contents += run_module_tmplt % myD
            #
            count += 1
        #
        if not hasValue:
            return
        #
        contents += '</tr>\n'
        self._dataInfo['run_workflow_module'] = contents

    def __depictLevel3TaskInfo(self):
        """
        """
        realFlowList = self._statusDB.getRealFlow(depositionid=self._reqObj.getValue('identifier'), instid=self._reqObj.getValue('instance'),
                                                  classid=self._reqObj.getValue('classID'))
        if not realFlowList:
            return ''
        #
        task_tmplt = self._getPageTemplate('task_tmplt')
        log_tmplt = self._getPageTemplate('download_task_log_tmplt')
        #
        contents = '<tr>\n'
        count = 0
        for dir in realFlowList:  # pylint: disable=redefined-builtin
            if count == self.__MaxBoxTask:
                count = 0
                contents += '</tr>\n<tr>\n'
            #
            myD = self.__initializeMyD()
            myD = self.__expandMyD(myD, dir, ('wf_task_id', 'task_status', 'task_type', 'status_timestamp'))
            #
            wf = self.__wfWorkFlowInfo[myD['wf_task_id']]
            myD = self.__expandMyD(myD, wf, ('name', 'description', 'reference'))
            #
            myD['log_file'] = self.__getTaskLogFile(log_tmplt, myD)
            #
            if myD['task_status'] == 'waiting':
                myD['base_url'] = self._processBaseUrl(myD['classID'])
                myD['style'] = 'style ="color:black;display:block;"'
                myD['open_interface'] = self.__interface_tmplt % myD
            else:
                myD['open_interface'] = ''
            #
            contents += task_tmplt % myD
            count += 1
        #
        contents += '</tr>\n'
        return contents

    def __initializeMyD(self):
        """
        """
        myD = {}
        for item in ('identifier', 'sessionid', 'annotator', 'method', 'urlmethod', 'instance', 'classID'):
            myD[item] = self._reqObj.getValue(item)
        #
        if myD['method'] and (not myD['urlmethod']):
            myD['urlmethod'] = u_quote(myD['method'])
        #
        return myD

    def __expandMyD(self, myD, sourceD, itemTuple):
        """
        """
        for item in itemTuple:
            myItem = item
            if item == 'wf_inst_id':
                myItem = 'instance'
            elif item == 'wf_class_id':
                myItem = 'classID'
            #
            if sourceD and (item in sourceD) and sourceD[item]:
                if item == 'status_timestamp':
                    myD[myItem] = getTimeString(sourceD[item])
                else:
                    myD[myItem] = str(sourceD[item])
            else:
                myD[myItem] = ''
            #
        #
        return myD

    def __processDownLoadCifFile(self, myD, delimiter):
        """
        """
        try:
            pI = PathInfo(siteId=self._siteId, sessionPath=self.__sessionPath, verbose=self._verbose, log=self._lfh)
            filePath = pI.getFilePath(dataSetId=myD['identifier'], wfInstanceId=myD['instance'], contentType='model',
                                      formatType='pdbx', fileSource='wf-instance', versionId='latest', partNumber='1')

            if filePath and os.access(filePath, os.F_OK):
                return delimiter + self.__download_tmplt % myD
            #
        except:  # noqa: E722 pylint: disable=bare-except
            traceback.print_exc(file=self._lfh)
        #
        return ''

    def __getTaskLogFile(self, log_tmplt, myD):
        """
        """
        self._reqObj.setValue('taskID', myD['wf_task_id'])
        self._reqObj.setValue('reference', myD['reference'])
        logUtil = LogFileUtil(reqObj=self._reqObj, verbose=self._verbose, log=self._lfh)
        logFilePath = logUtil.getLogFile()
        if logFilePath:
            return log_tmplt % myD
        #
        return ''
