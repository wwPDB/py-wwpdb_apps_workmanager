##
# File:  Level1Util.py
# Date:  18-Mar-2016
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
# from types import *

from wwpdb.utils.config.ConfigInfoApp import ConfigInfoAppCommon
from wwpdb.io.file.mmCIFUtil import mmCIFUtil
from wwpdb.apps.workmanager.depict.DepictBase import DepictBase
from wwpdb.apps.workmanager.depict.DepictContent import DepictContent
from wwpdb.apps.workmanager.depict.ReadConFigFile import dumpPickleFile


class Level1Util(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(Level1Util, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #
        self.__sObj = self._reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        self.__userID = self._reqObj.getValue('username').upper()
        self.__tab_def_id = ''
        self.__tab_count_id = ''
        self.__resultMap = {}
        # tableContentMap = { 'tab_count_id_table_id': { 'data-field': [fildlist], 'pkl': tableContentPickleFile,
        #                    'sql': sql, 'sql_selection': sql_selection, 'tab_count_id': 'tab_count_id',
        #                    'entry_count': { 'tab_count': [ items ], 'status_count': [ items ] } } }
        self.__tableContentMap = {}

    def run(self):
        """
        """
        tabList = self.__getTabList()
        if not tabList:
            return ''
        #
        self.__countMap = {}  # pylint: disable=attribute-defined-outside-init
        self._getUserInfoDict()
        #
        self._dataInfo['ann_selection'] = self._getAnnotatorSelection()
        count = 1
        all_tab_ids = []
        for tab in tabList:
            self.__tab_def_id = tab
            self.__tab_count_id = 'id_' + str(count)
            all_tab_ids.append(self.__tab_count_id)
            if 'firstTab' not in self.__resultMap:
                self.__resultMap['firstTab'] = self.__tab_count_id
            #
            self._dataInfo['tab_id'] = self.__tab_count_id
            self.__processTableDefinition()
            self.__processTabDefinition()
            count += 1
        #
        self.__resultMap['all_tab_ids'] = ','.join(all_tab_ids)
        #
        for _k, v in self.__tableContentMap.items():
            if not v['tab_count_id'] in self.__countMap:
                continue
            #
            v['entry_count'] = self.__countMap[v['tab_count_id']]
        #
        dumpPickleFile(self.__sessionPath, 'TableContentMap.pkl', self.__tableContentMap)
        depContUtil = DepictContent(reqObj=self._reqObj, statusDB=self._statusDB, conFigObj=self._conFigObj, verbose=self._verbose, log=self._lfh)
        self.__resultMap['entry_count_map'] = depContUtil.depictTableContent('all')
        #
        return ''

    def getResult(self, input_type='', return_type='string', delimiter=','):
        """
        """
        if delimiter == 'newline':
            delimiter = '\n'
        elif delimiter == 'empty':
            delimiter = ''
        #
        if input_type and (input_type in self.__resultMap):
            return self._processResult(self.__resultMap[input_type], return_type, delimiter)
        #
        if return_type == 'dict':
            return '{}'
        elif return_type == 'list':
            return '[]'
        else:
            return ''

    def getEnum(self, input_type=''):
        """
        """
        if not input_type:
            return '[]'
        #
        enum_list = getattr(self, "_get_%s_enum_list" % input_type)()
        #
        if enum_list:
            return self._processResult(enum_list, 'list', ',')
        #
        return '[]'

    def __getTabList(self):
        """
        """
        templateID = 'default_template'
        #
        if ('user_template_mapping' in self._conFigObj) and (self.__userID in self._conFigObj['user_template_mapping']):
            templateID = self._conFigObj['user_template_mapping'][self.__userID]
        #
        if ('level1_template_definition' in self._conFigObj) and (templateID in self._conFigObj['level1_template_definition']):
            # return self._conFigObj['level1_template_definition'][templateID]
            templateList = []
            for dirMap in self._conFigObj['level1_template_definition'][templateID]:
                if ('condition_type' not in dirMap) or ('condition_value' not in dirMap):
                    templateList.append(dirMap['tab_id'])
                elif dirMap['condition_type'] == 'statusDB':
                    self._connectStatusDB()
                    if self._statusDB.isTableValid(table=dirMap['condition_value']):
                        templateList.append(dirMap['tab_id'])
                    #
                #
            #
            return templateList
        #
        return []

    def __processTableDefinition(self):
        """
        """
        if ('table_definition' not in self._conFigObj) or (self.__tab_def_id not in self._conFigObj['table_definition']):
            return
        #
        dataList = []
        tableLoad = []
        table_keys = sorted(self._conFigObj['table_definition'][self.__tab_def_id].keys())
        for key in table_keys:
            tableDef = self._conFigObj['table_definition'][self.__tab_def_id][key]
            tableContentFile = 'table_content_' + str(len(self.__tableContentMap) + 1) + '.pkl'
            tableLoad.append([tableDef['load'], tableDef['table_id'], tableContentFile])
            dataD = {}
            dataD['tab_id'] = self.__tab_count_id
            dataD['table_id'] = tableDef['table_id']
            dataD['display'] = tableDef['display']
            if 'table_title' in tableDef:
                dataD['table_title'] = tableDef['table_title']
            #
            dataD['table_option'] = tableDef['option']
            #
            if 'column' in tableDef:
                columnList, dataField = self.__getColumnListandDataField(tableDef['table_id'], tableDef['column'])
                dataD['column_labels'] = '\n'.join(columnList)
                self.__processTableContents(tableDef, dataField, tableContentFile)
            elif 'binding_function' in tableDef:
                tableMap = {}
                tableMap['tab_count_id'] = self.__tab_count_id
                tableMap['binding_function'] = tableDef['binding_function']
                tableMap['pkl'] = tableContentFile
                #
                if 'binding_class' in tableDef:
                    tableMap['binding_class'] = tableDef['binding_class']
                    self._processBindingClass(tableDef['binding_class'])
                    classUtil = self._UtilClass[tableDef['binding_class']]
                    columnDef, _data = getattr(classUtil, '%s' % tableDef['binding_function'])()
                else:
                    columnDef, _data = getattr(self, '%s' % tableDef['binding_function'])()
                #
                self.__tableContentMap[self.__tab_count_id + '_' + tableDef['table_id']] = tableMap
                columnList, dataField = self.__getColumnListandDataField(tableDef['table_id'], columnDef)
                dataD['column_labels'] = '\n'.join(columnList)
            #
            dataList.append(dataD)
        #
        if dataList:
            self._dataInfo['data_table_tmplt'] = dataList
        #
        if tableLoad:
            if 'table_id_map' not in self.__resultMap:
                self.__resultMap['table_id_map'] = {}
            #
            self.__resultMap['table_id_map'][self.__tab_count_id] = tableLoad
        #

    def __getColumnListandDataField(self, table_id, columnDefList):
        """
        """
        columnList = []
        dataField = []
        for vDict in columnDefList:
            columnDef = '<th'
            dataField.append(vDict['data-field'])
            for item in ('data-field', 'data-sortable', 'data-visible', 'data-sorter', 'data-sort-name', 'data-cell-style'):
                if item == 'data-visible':
                    key = self.__userID + '-' + self.__tab_def_id + '-' + table_id + '-' + vDict['data-field']
                    all_key = 'all-' + self.__tab_def_id + '-' + table_id + '-' + vDict['data-field']
                    if ('user_tab_table_column_config' in self._conFigObj) and (key in self._conFigObj['user_tab_table_column_config']):
                        if self._conFigObj['user_tab_table_column_config'][key] == 'false':
                            columnDef += ' ' + item + '="false"'
                        #
                    elif ('user_tab_table_column_config' in self._conFigObj) and (all_key in self._conFigObj['user_tab_table_column_config']):
                        if self._conFigObj['user_tab_table_column_config'][all_key] == 'false':
                            columnDef += ' ' + item + '="false"'
                        #
                    elif item in vDict:
                        columnDef += ' ' + item + '="' + vDict[item] + '"'
                    #
                elif item in vDict:
                    columnDef += ' ' + item + '="' + vDict[item] + '"'
                #
            #
            columnDef += '>' + vDict['label'] + '</th>'
            columnList.append(columnDef)
        #
        return columnList, dataField

    def __processTableContents(self, tableDef, dataField, tableContentFile):
        """
        """
        tableMap = {}
        tableMap['tab_count_id'] = self.__tab_count_id
        tableMap['data-field'] = dataField
        tableMap['pkl'] = tableContentFile
        for extraInfo in ('order_condition', 'sort_function'):
            if (extraInfo in tableDef) and tableDef[extraInfo]:
                tableMap[extraInfo] = tableDef[extraInfo]
            #
        #
        sql_selection = tableDef['sql_selection']
        if 'sql_where_condition' in tableDef:
            # sql_where_condition = tableDef['sql_where_condition']
            if 'sql_variable' in tableDef:
                if tableDef['sql_variable'] == 'retired_annotator':
                    myD = {}
                    myD['retired_annotator'] = 'Not_Found'
                    self._connectStatusDB()
                    if self._statusDB:
                        rtList = self._statusDB.getRetiredAnnotatorInitials()
                        if rtList:
                            myD['retired_annotator'] = "', '".join(rtList)
                        #
                    #
                    tableMap['sql'] = sql_selection + ' ' + tableDef['sql_where_condition'] % myD
                else:
                    # assume that sql_variable is 'initials' & 'site'
                    tableMap['sql'] = sql_selection + ' ' + tableDef['sql_where_condition'] % self._userInfo
                #
            else:
                tableMap['sql'] = sql_selection + ' ' + tableDef['sql_where_condition']
            #
        else:
            tableMap['sql_selection'] = sql_selection
        #
        self.__tableContentMap[self.__tab_count_id + '_' + tableDef['table_id']] = tableMap

    def __processTabDefinition(self):
        """
        """
        secList = []
        if ('tab_definition_template' in self._conFigObj) and (self.__tab_def_id in self._conFigObj['tab_definition_template']):
            secList = self._conFigObj['tab_definition_template'][self.__tab_def_id]
        #
        if not secList:
            return
        #
        for secD in secList:
            if secD['template_type'] == 'html':
                self.__processHtmlTemplate(secD)
            #
        #

    def __processHtmlTemplate(self, secD):
        """
        """
        myParaD = self.__getPreProcessParameter(secD)
        page = self.getPageText(page_id=secD['template_id'], paraD=myParaD)
        if page:
            if not secD['section_id'] in self.__resultMap:
                self.__resultMap[secD['section_id']] = []
            #
            self.__resultMap[secD['section_id']].append(page)
        #

    def __getPreProcessParameter(self, secD):
        """
        """
        template_id = secD['template_id']
        paraD = {}
        key = self.__tab_def_id + ',' + template_id
        if ('tab_preprocess_mapping' not in self._conFigObj) or (key not in self._conFigObj['tab_preprocess_mapping']):
            return paraD
        #
        myD = {}
        if ('count_type' in secD) and secD['count_type'] and ('count_variables' in secD) and secD['count_variables'] and \
           ('count_template' in secD) and secD['count_template']:
            if self.__tab_count_id not in self.__countMap:
                self.__countMap[self.__tab_count_id] = {}
            #
            itemList = secD['count_variables'].split(',')
            self.__countMap[self.__tab_count_id][secD['count_type']] = itemList
            #
            tmplt = self._getPageTemplate(secD['count_template'])
            text = ''
            for item in itemList:
                if text:
                    text += ', '
                #
                text += tmplt % {'type': secD['count_type'], 'variable': item, 'tab_id': self.__tab_count_id}
            #
            myD['counts'] = text
        #
        for paraMap in self._conFigObj['tab_preprocess_mapping'][key]:
            if myD:
                paraD[paraMap['variable']] = self._preProcessParameterMap(paraMap['value'], myD)
            else:
                paraD[paraMap['variable']] = paraMap['value']
            #
        #
        return paraD

    def _get_entry_by_sg_center_enum_list(self):
        """
        """
        list = []  # pylint: disable=redefined-builtin
        cICommon = ConfigInfoAppCommon(self._siteId)
        sg_center_file = cICommon.get_sg_center_file_path()
        if os.access(sg_center_file, os.F_OK):
            cifObj = mmCIFUtil(filePath=sg_center_file)
            dlist = cifObj.GetValue('pdbx_SG_project')
            list.append(['', ''])
            for ldir in dlist:
                list.append([ldir['full_name_of_center'], ldir['full_name_of_center']])
            #
        #
        return list
