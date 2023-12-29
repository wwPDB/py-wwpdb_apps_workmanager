##
# File:  ReadConFigFile.py
# Date:  16-Mar-2016
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

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

import os
import sys
from wwpdb.io.file.mmCIFUtil import mmCIFUtil


class ReadConFigFile(object):
    """
    """
    def __init__(self, reqObj=None, configFile=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """
        """
        self.__reqObj = reqObj
        self.__configFile = configFile
        # self.__verbose = verbose
        # self.__lfh = log
        self.__topPath = self.__reqObj.getValue("TemplatePath")
        self.__configPath = os.path.join(self.__topPath, self.__configFile)
        #
        self.__sObj = self.__reqObj.newSessionObj()
        # self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()
        (base, _ext) = os.path.splitext(self.__configFile)
        self.__pickleFile = base + '.pkl'
        self.__picklePath = os.path.join(self.__sessionPath, self.__pickleFile)
        #

    def read(self):
        """
        """
        Dict = {}
        if os.access(self.__picklePath, os.F_OK):
            Dict = loadPickleFile(self.__sessionPath, self.__pickleFile)
            return Dict
        #
        cifObj = mmCIFUtil(filePath=self.__configPath)
        for item in ('user_template_mapping', 'user_tab_table_column_config', 'level1_template_definition', 'tab_definition_template',
                     'tab_preprocess_mapping', 'page_template', 'page_template_alias', 'page_template_parameter', 'function_parameter',
                     'ui_input_where_condition_binding', 'ui_input_dependence', 'table_data_field_binding'):
            vMap = {}
            try:
                vMap = getattr(self, "_read_%s" % item)(cifObj.GetValue(item))
            except:  # noqa: E722 pylint: disable=bare-except
                vMap = self.__read_list(cifObj.GetValue(item))
            #
            if vMap:
                Dict[item] = vMap
            #
        #
        tabDict = {}
        foundEmpty = False
        for item in ('tab_definition_table', 'table_definition', 'table_binding_definition', 'table_option_definition',
                     'table_column_definition', 'tab_table_sql_binding', 'sql_selection_definition'):
            try:
                tabDict[item] = getattr(self, "_read_%s" % item)(cifObj.GetValue(item))
            except:  # noqa: E722 pylint: disable=bare-except
                tabDict[item] = self.__read_list(cifObj.GetValue(item))
            #
            if not tabDict[item]:
                foundEmpty = True
            #
        #
        if tabDict and (not foundEmpty):
            Dict['table_definition'] = self.__processTableDefinition(tabDict)
        #
        dumpPickleFile(self.__sessionPath, self.__pickleFile, Dict)
        #
        return Dict

    def _read_user_template_mapping(self, vList):
        """
        """
        return self.__read_as_map(vList, 'user_id', 'template_id')

    def _read_user_tab_table_column_config(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            data = []
            for item in ('user_id', 'tab_id', 'table_id', 'data-field'):
                data.append(vMap[item])
            #
            Map['-'.join(data)] = vMap['data-visible']
        #
        return Map

    def _read_level1_template_definition(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            if not vMap['id'] in Map:
                Map[vMap['id']] = []
            #
            Map[vMap['id']].append(vMap)
        #
        return Map

    def _read_page_template(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def _read_page_template_alias(self, vList):
        """
        """
        return self.__read_as_map(vList, 'id', 'page_id')

    def _read_page_template_parameter(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            if not vMap['page_id'] in Map:
                Map[vMap['page_id']] = [[], []]
            #
            if vMap['preprocess'].lower() == 'y':
                Map[vMap['page_id']][0].append(vMap)
            else:
                Map[vMap['page_id']][1].append(vMap)
            #
        #
        return Map

    def _read_table_option_definition(self, vList):
        """
        """
        return self.__read_as_map(vList, 'id', 'option')

    def _read_table_binding_definition(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def _read_table_column_definition(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def _read_tab_table_sql_binding(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            key = vMap['tab_id'] + '_' + vMap['table_id']
            Map[key] = vMap
        #
        return Map

    def _read_sql_selection_definition(self, vList):
        """
        """
        return self.__read_as_map(vList, 'id', 'sql')

    def _read_ui_input_where_condition_binding(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def _read_ui_input_dependence(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def _read_table_data_field_binding(self, vList):
        """
        """
        return self.__read_as_Dictmap(vList)

    def __read_as_Dictmap(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            Map[vMap['id']] = vMap
        #
        return Map

    def __read_as_map(self, vList, key_item, value_item):
        """
        """
        Map = {}
        for vMap in vList:
            Map[vMap[key_item]] = vMap[value_item]
        #
        return Map

    def __read_list(self, vList):
        """
        """
        Map = {}
        for vMap in vList:
            if not vMap['id'] in Map:
                Map[vMap['id']] = []
            #
            Map[vMap['id']].append(vMap)
        #
        return Map

    def __processTableDefinition(self, inDict):
        """ outDict = { 'tab_def_id': { 'table_id': { 'table_id': 'table_id', 'display': 'default_display', 'option': 'option_definition',
                        'load': 'default_load', 'column': [ {column_definition} ], 'sql_selection': 'sql_selection', 'sort_function':
                        'sort_function', 'sql_where_condition': 'sql_where_condition', 'sql_variable': 'sql_variable' } } }
        """
        outDict = {}
        for tab_id, vList in inDict['tab_definition_table'].items():
            tableList = {}
            for vDict in vList:
                option = ''
                if vDict['table_option_id'] in inDict['table_option_definition']:
                    option = inDict['table_option_definition'][vDict['table_option_id']]
                #
                tableDef = self.__getSqlInfo(tab_id + '_' + vDict['table_id'], inDict)
                column = self.__getTableColumns(vDict['table_definition_id'], inDict)
                if column:
                    if tableDef:
                        tableDef['column'] = column
                    #
                else:
                    tableDef = {}
                #
                bindingTableDef = {}
                if vDict['table_definition_id'] in inDict['table_binding_definition']:
                    bindingTableDef = inDict['table_binding_definition'][vDict['table_definition_id']]
                #
                if option and (tableDef or bindingTableDef):
                    tableDict = {}
                    tableDict['table_id'] = vDict['table_id']
                    tableDict['display'] = vDict['default_display']
                    tableDict['load'] = vDict['default_load']
                    if 'table_title' in vDict:
                        tableDict['table_title'] = vDict['table_title']
                    #
                    tableDict['option'] = option
                    if tableDef:
                        for k, v in tableDef.items():
                            tableDict[k] = v
                        #
                    else:
                        for item in ('binding_function', 'binding_class'):
                            if item in bindingTableDef:
                                tableDict[item] = bindingTableDef[item]
                            #
                        #
                    #
                    tableList[vDict['table_id']] = tableDict
                #
            #
            if tableList:
                outDict[tab_id] = tableList
            #
        #
        return outDict

    def __getTableColumns(self, table_definition_id, inDict):
        """
        """
        columnList = []
        if ('table_definition' not in inDict) or (table_definition_id not in inDict['table_definition']):
            return columnList
        #
        for vDict in inDict['table_definition'][table_definition_id]:
            if ('table_column_definition' not in inDict) or (vDict['column_definition'] not in inDict['table_column_definition']):
                return []
            #
            columnList.append(inDict['table_column_definition'][vDict['column_definition']])
        #
        return columnList

    def __getSqlInfo(self, key, inDict):
        """
        """
        myD = {}
        if ('tab_table_sql_binding' not in inDict) or (key not in inDict['tab_table_sql_binding']):
            return myD
        #
        # sql_selection = ''
        # sql_where_condition = ''
        # sql_variable = ''
        # sort_function = ''
        if ('select_definition_id' in inDict['tab_table_sql_binding'][key]) and inDict['tab_table_sql_binding'][key]['select_definition_id']:
            select_id = inDict['tab_table_sql_binding'][key]['select_definition_id']
            if ('sql_selection_definition' in inDict) and (select_id in inDict['sql_selection_definition']) and inDict['sql_selection_definition'][select_id]:
                myD['sql_selection'] = inDict['sql_selection_definition'][select_id]
            #
        #
        if not myD:
            return myD
        #
        for options in (('sql_where_condition', 'where_condition'), ('order_condition', 'additional_order_condition'),
                        ('sql_variable', 'variable'), ('sort_function', 'additional_sort_function')):
            if (not options[1] in inDict['tab_table_sql_binding'][key]) or (not inDict['tab_table_sql_binding'][key][options[1]]):
                continue
            #
            myD[options[0]] = inDict['tab_table_sql_binding'][key][options[1]]
        #
        return myD


def dumpPickleFile(sessionPath, filename, data):
    """
    """
    pickle_file = os.path.join(sessionPath, filename)
    f = open(pickle_file, 'wb')
    pickle.dump(data, f)
    f.close()


def loadPickleFile(sessionPath, filename):
    """
    """
    pickle_file = os.path.join(sessionPath, filename)
    if not os.access(pickle_file, os.F_OK):
        return None
    #
    f = open(pickle_file, 'rb')
    data = pickle.load(f)
    f.close()
    return data
