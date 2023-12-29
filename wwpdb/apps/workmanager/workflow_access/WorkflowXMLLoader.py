##
# File:  WorkflowXMLLoader.py
# Date:  12-June-2015
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2015 wwPDB

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
from xml.dom import minidom
#
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.apps.workmanager.workflow_access.OrderedDict import OrderedDict


class WorkflowXMLLoader(object):
    """
    """
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):  # pylint:  disable=unused-argument
        """
        """
        self.__siteId = siteId
        # self.__verbose = verbose
        # self.__lfh = log
        self.__cI = ConfigInfo(self.__siteId)
        self.__workFlowXMLPath = self.__cI.get("SITE_WF_XML_PATH")
        #
        self.__metaDataInfo = {}
        self.__workFlowInfo = OrderedDict()

    def loadWorkFlowXMLFile(self, XMLFile=None):
        if not XMLFile:
            return
        #
        xmlfile = os.path.join(self.__workFlowXMLPath, XMLFile)
        if not os.access(xmlfile, os.F_OK):
            return
        #
        xmlDoc = minidom.parse(xmlfile)
        self.__readMetaDataInfo(xmlDoc)
        self.__readWorkFlowInfo(xmlDoc)

    def getMetaDataInfo(self):
        return self.__metaDataInfo

    def getWorkFlowInfo(self):
        return self.__workFlowInfo

    def __readMetaDataInfo(self, xmlDoc):
        metadata_version = xmlDoc.getElementsByTagName("wf:version")
        for item in ('author', 'major', 'date', 'id', 'name'):
            self.__metaDataInfo[item] = str(metadata_version[0].getAttribute(item))
        #

    def __readWorkFlowInfo(self, xmlDoc):
        index = 0
        #
        node = xmlDoc.getElementsByTagName("wf:entryPoint")
        task = self.__parseTaskNode(node[0])
        task['type'] = 'Entry-point'
        self.__workFlowInfo.insert(index, task['taskID'], task)
        index += 1

        nodes = xmlDoc.getElementsByTagName("wf:task")
        for node in nodes:
            task = self.__parseTaskNode(node)
            self.__workFlowInfo.insert(index, task['taskID'], task)
            index += 1
        #
        node = xmlDoc.getElementsByTagName("wf:exitPoint")
        task = self.__parseTaskNode(node[0])
        task['type'] = 'Exit-point'
        self.__workFlowInfo.insert(index, task['taskID'], task)

    def __parseTaskNode(self, node):
        task = {}
        for item in ('taskID', 'name', 'nextTask', 'breakpoint', 'reference', 'exceptionID'):
            if node.hasAttribute(item):
                task[item] = str(node.getAttribute(item))
            #
        #
        if node.hasChildNodes():
            for childnode in node.childNodes:
                if childnode.nodeType != node.ELEMENT_NODE:
                    continue
                #
                if childnode.tagName == 'wf:description':
                    task['description'] = str(childnode.firstChild.data)
                elif childnode.tagName == 'wf:workflow':
                    task['type'] = 'workflow'
                    task['file'] = str(childnode.getAttribute('file'))
                    task['classID'] = str(childnode.getAttribute('classID'))
                else:
                    for item in ('process', 'decision', 'manual'):
                        if childnode.tagName == 'wf:' + item:
                            task['type'] = item
                        #
                    #
                #
            #
        #
        return task


if __name__ == '__main__':
    loader = WorkflowXMLLoader(siteId='WWPDB_DEPLOY_TEST', verbose=True, log=sys.stderr)
    loader.loadWorkFlowXMLFile('Annotation.xml')
    info = loader.getMetaDataInfo()
    print(info)
    wfinfo = loader.getWorkFlowInfo()
    print(wfinfo[0:1])
    print(wfinfo['T1'])
    print(wfinfo)
    for key, mytask in wfinfo.items():
        print(key)
        print(mytask)
    #
    values = wfinfo.values()
    for v in values:
        print(v)
