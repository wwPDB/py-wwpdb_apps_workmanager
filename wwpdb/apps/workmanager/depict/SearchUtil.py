##
# File:  SearchUtil.py
# Date:  04-April-2016
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

from wwpdb.apps.workmanager.db_access.ContentDbApi import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.depict.ReadConFigFile import ReadConFigFile, dumpPickleFile, loadPickleFile


class SearchUtil(object):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        self.__siteId = self.__reqObj.getValue("WWPDB_SITE_ID")
        # self.__topPath = self.__reqObj.getValue("TemplatePath")
        #
        self.__statusDB = None
        self.__contentDB = None
        self.__conFigObj = None
        #
        self.__sObj = self.__reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        #

    def updateSql(self):
        """
        """
        index = self.__reqObj.getValue('index')
        search_type = self.__reqObj.getValue('search_type')
        value = self.__reqObj.getValue('value')
        if (not index) or (not search_type):
            return
        #
        tableContentMap = loadPickleFile(self.__sessionPath, 'TableContentMap.pkl')
        if (not tableContentMap) or (index not in tableContentMap):
            return
        #
        self.__readConFigObj()
        if (not self.__conFigObj) or ('ui_input_where_condition_binding' not in self.__conFigObj) or \
           (search_type not in self.__conFigObj['ui_input_where_condition_binding']):
            return
        #
        myD = {}
        if ('dependence_id' in self.__conFigObj['ui_input_where_condition_binding'][search_type]) and \
           self.__conFigObj['ui_input_where_condition_binding'][search_type]['dependence_id']:
            myD['value'] = self.__processDependence(self.__conFigObj['ui_input_where_condition_binding'][search_type]['dependence_id'], value)
        elif search_type == 'entry_by_ids':
            self.__connectStatusDB()
            _error_message, entryIdList = self.__statusDB.getEntryIdListFromInputIdString(value)
            myD['value'] = "', '".join(entryIdList)
        elif (search_type == 'user_by_ids') or (search_type == 'dep_by_ids') or (search_type == 'group_by_ids'):
            myList = []
            for ID in value.strip().split(','):
                myList.append(ID.strip())
            #
            myD['value'] = "', '".join(myList)
        else:
            myD['value'] = value
        #
        where_condition = self.__conFigObj['ui_input_where_condition_binding'][search_type]['where_condition'] % myD
        tableContentMap[index]['sql'] = tableContentMap[index]['sql_selection'] + ' ' + where_condition
        dumpPickleFile(self.__sessionPath, 'TableContentMap.pkl', tableContentMap)

    def __readConFigObj(self):
        """
        """
        readUtil = ReadConFigFile(reqObj=self.__reqObj, configFile='level1_config.cif', verbose=self.__verbose, log=self.__lfh)
        self.__conFigObj = readUtil.read()

    def __processDependence(self, dependence_id, value):
        """
        """
        if (not self.__conFigObj) or ('ui_input_dependence' not in self.__conFigObj) or (dependence_id not in self.__conFigObj['ui_input_dependence']):
            return value
        #
        sql = self.__conFigObj['ui_input_dependence'][dependence_id]['sql']
        if value:
            myD = {}
            myD['value'] = value
            sql = sql % myD
        #
        retList = []
        if self.__conFigObj['ui_input_dependence'][dependence_id]['db'] == 'contentDB':
            self.__connectContentDB()
            retList = self.__contentDB.runSelectSQL(sql)
        else:
            self.__connectStatusDB()
            retList = self.__statusDB.runSelectSQL(sql)
        #
        idList = []
        if retList:
            for dataD in retList:
                idList.append(dataD['id'])
            #
        #
        return "', '".join(idList)

    def __connectStatusDB(self):
        """
        """
        if not self.__statusDB:
            self.__statusDB = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #

    def __connectContentDB(self):
        """
        """
        if not self.__contentDB:
            self.__contentDB = ContentDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #
