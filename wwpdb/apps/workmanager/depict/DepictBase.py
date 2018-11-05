##
# File:  DepictBase.py
# Date:  17-Mar-2016
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


import __builtin__,os,sys
from types import *

from wwpdb.api.facade.ConfigInfo                    import ConfigInfo
from wwpdb.apps.workmanager.db_access.ContentDbApi  import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatsUtil     import StatsUtil
from wwpdb.apps.workmanager.db_access.StatusDbApi   import StatusDbApi

class DepictBase(object):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        self._reqObj    = reqObj
        self._conFigObj = conFigObj
        self._verbose   = verbose
        self._lfh       = log
        self._siteId    = self._reqObj.getValue("WWPDB_SITE_ID")
        self._topPath   = self._reqObj.getValue("TemplatePath")
        #
        self.__urlMap   = {}
        self._UtilClass = {}
        self._userInfo  = {}
        self._dataInfo  = {}
        self._uInfoFlag = False
        self._statusDB  = statusDB
        self._contentDB = None
        self.__getUrlMap()
    
    def getPageText(self, page_id='', paraD={}):
        """
        """
        page_template,alias_page_id = self.__getPageTemplateAndAliasID(page_id)
        if not page_template:
            return ''
        #
        if not 'page_template_parameter' in self._conFigObj:
            return ''
        #
        pageD = self._conFigObj['page_template'][alias_page_id]
#       if ('dependence' in pageD) and (not pageD['dependence'] in self._dataInfo):
#           return ''
#       #
        if paraD:
            page_template = self._preProcessParameterMap(page_template, paraD)
        #
        page_parameter = self._conFigObj['page_template_parameter'][alias_page_id]
        page_template = self.__preProcessParameter(page_id, alias_page_id, page_template, page_parameter[0])
        #
        return_text = ''
        if ('repeat' in pageD) and (pageD['repeat'] == 'yes') and (page_id in self._dataInfo):
            while len(self._dataInfo[page_id]) > 0:
                 text = self.__processParameter(page_id, alias_page_id, page_template, page_parameter[1])
                 if return_text:
                     return_text += '\n'
                 return_text += text
                 self._dataInfo[page_id].pop(0)
            #
        else:
            return_text = self.__processParameter(page_id, alias_page_id, page_template, page_parameter[1])
        #
        return return_text

    def getDataResult(self, input_type='', return_type='string', delimiter=','):
        """
        """
        if delimiter == 'newline':
            delimiter = '\n'
        elif delimiter == 'empty':
            delimiter = ''
        #
        if input_type and (input_type in self._dataInfo):
            return self._processResult(self._dataInfo[input_type], return_type, delimiter)
        #
        if return_type == 'dict':
            return {}
        elif return_type == 'list':
            return []
        else:
            return ''

    def _getPageTemplate(self, page_id):
        """
        """
        if (not 'page_template' in self._conFigObj) or (not page_id) or (not page_id in self._conFigObj['page_template']):
            return ''
        #
        pageD = self._conFigObj['page_template'][page_id]
        page_template = pageD['page']
        if pageD['type'] == 'file':
            page_template = self.__readTemplate(pageD['page'])
        #
        return page_template

    def _preProcessParameterMap(self, template, myD):
        """
        """
        for k,v in myD.items():
            template = template.replace('%(' + k + ')s', v)
        #
        return template

    def _getUserInfo(self, parameter):
        """
        """
        self._getUserInfoDict()
        #
        val = ''
        if self._userInfo and (parameter in self._userInfo):
            val = self._userInfo[parameter]
        #
        return val

    def _getUserInfoDict(self):
        """
        """
        if self._uInfoFlag:
            return
        #
        self._connectStatusDB()
        #
        if self._statusDB:
            if self._reqObj.getValue('username') and self._reqObj.getValue('password'):
                self._userInfo = self._statusDB.Autenticate(self._reqObj.getValue('username'), self._reqObj.getValue('password'))
            #
            if not self._userInfo and self._reqObj.getValue('annotator'):
                self._userInfo = self._statusDB.getUserByInitial(initial=self._reqObj.getValue('annotator'))
            #
            if not self._userInfo and self._reqObj.getValue('initials'):
                self._userInfo = self._statusDB.getUserByInitial(initial=self._reqObj.getValue('initials'))
            #
        #
        self._uInfoFlag = True

    def _get_entry_by_initial_enum_list(self):
        """
        """
        self._getUserInfoDict()
        rows = self._statusDB.getAnnUser(self._userInfo['site'])
        list = []
        for dir in rows:
            list.append( [ str(dir['initials']), str(dir['first_name']) + ' ' +  str(dir['last_name']) ] )
        #
        list.sort(key = lambda data: data[1])
        list.insert(0, [ '', '' ] )
        return list

    def _getAnnotatorSelection(self):
        """
        """
        AnnotatorInfo = self._get_entry_by_initial_enum_list()
        return self.__getSelectionOption(AnnotatorInfo)

    def _getPrivilegeTableRows(self):
        """
        """
        rows = self.__getSiteUserInfo()
        if not rows:
            return
        #
        table_row1 = []
        table_row2 = []
        for dir in rows:
            if str(dir['active']) != '0':
                continue
            #
            dir['checked'] = ''
            dir['disabled'] = ''
            if dir['user_name'] == self._userInfo['user_name']:
                dir['disabled'] = 'disabled="true"'
            #
            if str(dir['code']).upper() == 'ANN':
                dir['value'] = 'LANN'
                table_row1.append(dir)
            elif str(dir['code']).upper() == 'LANN':
                dir['value'] = 'ANN'
                table_row2.append(dir)
            #
        #
        self._dataInfo['privilege_ann_table_row_tmplt'] = table_row1
        self._dataInfo['privilege_lead_table_row_tmplt'] = table_row2

    def _getGroupSelection(self):
        """
        """
        GroupInfo = []
        GroupInfo.append( [ '', '' ] )
        self._getUserInfoDict()
        if self._statusDB:
            rows = self._statusDB.getSiteGroup(self._userInfo['site'])
            for dir in rows:
                GroupInfo.append( [ str(dir['group_id']), str(dir['group_name']) ] )
            #
        #
        return self.__getSelectionOption(GroupInfo)

    def _getActiveTableRow(self):
        """
        """
        rows = self.__getSiteUserInfo()
        if not rows:
            return
        #
        for dir in rows:
            dir['checked'] = ''
            dir['value'] = str(dir['active'])
            if str(dir['active']) == '0':
                dir['checked'] = 'checked'
            #
            dir['disabled'] = ''
            if dir['user_name'] == self._userInfo['user_name']:
                dir['disabled'] = 'disabled="true"'
            #
        #
        self._dataInfo['atvice_user_table_row_tmplt'] = list(rows)

    def _connectStatusDB(self):
        """
        """
        if not self._statusDB:
            self._statusDB = StatusDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        #

    def _connectContentDB(self):
        """
        """
        if not self._contentDB:
            self._contentDB = ContentDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        #

    def _processResult(self, resultObj, return_type, delimiter):
        """
        """
        stringFlag = False
        if return_type == 'string':
            stringFlag = True
        #
        if type(resultObj) is DictType:
            return self.__writeDirValue(resultObj, delimiter, stringFlag)
        elif type(resultObj) is ListType:
            return self.__writeListValue(resultObj, delimiter, stringFlag)
        else:
            return str(resultObj)
        #

    def _processBindingClass(self, bindingClass):
        """
        """
        if bindingClass in self._UtilClass:
            return
        #
        if bindingClass == 'StatsUtil':
            self._UtilClass[bindingClass] = StatsUtil(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        #

    def _processBaseUrl(self, class_id):
        """
        """
        if class_id in self.__urlMap:
            return self.__urlMap[class_id]
        #
        return ''

    def __getUrlMap(self):
        """
        """
        mod_url_list = [ [ 'AnnMod', 'SITE_ANN_TASKS_URL' ], [ 'LigMod', 'SITE_LE_URL' ], [ 'LigModUI', 'SITE_LE_URL' ], \
                         [ 'SeqMod', 'SITE_SE_URL' ], [ 'TransMod', 'SITE_TRANS_EDITOR_URL' ], [ 'ValMod', 'SITE_VAL_TASKS_URL' ] ]
        #
        cI = ConfigInfo(self._siteId)
        for list in mod_url_list:
            self.__urlMap[list[0]] = cI.get(list[1])
        #

    def __getPageTemplateAndAliasID(self, page_id):
        """
        """
        alias_page_id = page_id
        page_template = self._getPageTemplate(page_id)
        if page_template:
            return page_template,alias_page_id
        #
        if ('page_template_alias' in self._conFigObj) and (page_id in self._conFigObj['page_template_alias']):
            tmp_page_id = self._conFigObj['page_template_alias'][page_id]
            tmp_page_template = self._getPageTemplate(tmp_page_id)
            if tmp_page_template:
                page_template = tmp_page_template
                alias_page_id = tmp_page_id
            #
        #
        return page_template,alias_page_id

    def __preProcessParameter(self, page_id, alias_page_id, template, paraList):
        """
        """
        myD = self.__getParameter(page_id, alias_page_id, paraList)
        if not myD:
            return template
        #
        return self._preProcessParameterMap(template, myD)
            
    def __processParameter(self, page_id, alias_page_id, template, paraList):
        """
        """
        myD = self.__getParameter(page_id, alias_page_id, paraList)
        if not myD:
            return template
        #
        return template % myD

    def __getParameter(self, page_id, alias_page_id, paraList):
        """
        """
        myD = {}
        if not paraList:
            return myD
        #
        for paraMap in paraList:
            myD[paraMap['variable']] = '' 
            if paraMap['type'] == 'page_template':
                myD[paraMap['variable']] = self.getPageText(page_id=paraMap['value'])
            elif paraMap['type'] == 'function':
                myD[paraMap['variable']] = self.__callFunc(alias_page_id, paraMap['variable'], paraMap['value'], myD)
            elif paraMap['type'] == 'sessionInfo':
                myD[paraMap['variable']] = self._reqObj.getValue(paraMap['value'])
            elif paraMap['type'] == 'userInfo':
                myD[paraMap['variable']] = self._getUserInfo(paraMap['value'])
            elif paraMap['type'] == 'dataInfo':
                if (page_id in self._dataInfo) and self._dataInfo[page_id]:
                    if paraMap['value'] in self._dataInfo[page_id][0]:
                        myD[paraMap['variable']] = self._dataInfo[page_id][0][paraMap['value']]
                    #
                elif ('data_for_all' in self._dataInfo) and self._dataInfo['data_for_all']:
                    if paraMap['value'] in self._dataInfo['data_for_all'][0]:
                        myD[paraMap['variable']] = self._dataInfo['data_for_all'][0][paraMap['value']]
                    #
                #
            elif paraMap['type'] == 'constant':
                myD[paraMap['variable']] = paraMap['value']
            #
        #
        return myD

    def __callFunc(self, page_id, variable, funcDef, myD):
        """
        """
        val = ''
        funcDef = funcDef.replace(' ', '')
        paraD = self.__getFuncParameter(page_id, variable, myD)
        if not paraD:
            paraD = self.__getFuncParameter(page_id, funcDef, myD)
        #
        if not paraD:
            paraD = self.__getFuncParameter(variable, funcDef, myD)
        #
        spList = funcDef.split(',')
        #
        if spList[0] == "self":
            if paraD:
                val = getattr(self, "%s" % spList[1])(**paraD)
            else:
                val = getattr(self, "%s" % spList[1])()
            #
        elif spList[0] in self._UtilClass:
            if paraD:
                val = getattr(self._UtilClass[spList[0]], "%s" % spList[1])(**paraD)
            else:
                val = getattr(self._UtilClass[spList[0]], "%s" % spList[1])()
            #
        #
        return val

    def __getFuncParameter(self, page_id, funcDef, myD):
        """
        """
        paraD = {}
        key = page_id + ',' + funcDef
        #
        if (not 'function_parameter' in self._conFigObj) or (not key in self._conFigObj['function_parameter']):
            return paraD
        #
        for paraMap in self._conFigObj['function_parameter'][key]:
            if ('value_type' in paraMap) and ('parameter_type' in paraMap) and paraMap['parameter_type'] == 'constant':
                paraD[paraMap['name']] = getattr(__builtin__, '%s' % paraMap['value_type'])(paraMap['value'])
            else:
                paraD[paraMap['name']] = paraMap['value']
            #
        #
        return paraD

    def __readTemplate(self, template_file):
        """
        """
        fPath = os.path.join(self._topPath, template_file)
        ifh = open(fPath, 'r')
        sIn = ifh.read()
        ifh.close()
        return sIn

    def __writeDirValue(self, obj, delimiter, stringFlag):
        """
        """
        quotation = "'"
        if stringFlag:
            quotation = ""
        #
        text = ''
        for k,v in obj.items():
            if text:
                text += delimiter
            #
            if type(v) is DictType:
                text += quotation + str(k) + quotation + ":" + self.__writeDirValue(v, delimiter, stringFlag)
            elif type(v) is ListType:
                text += quotation + str(k) + quotation + ":" + self.__writeListValue(v, delimiter, stringFlag)
            else:
                text += quotation + str(k) + quotation + ":" + quotation + str(v) + quotation
            #
        #
        if stringFlag:
            return text
        #
        text = text.replace(quotation + "False" + quotation, "false").replace(quotation + "True" + quotation, "true")
        text = text.replace(quotation + "false" + quotation, "false").replace(quotation + "true" + quotation, "true")
        return '{' + text + '}'

    def __writeListValue(self, obj, delimiter, stringFlag):
        """
        """
        quotation = "'"
        if stringFlag:
            quotation = ""
        #
        text = ''
        for v in obj:
            if text:
                text += delimiter
            #
            if type(v) is DictType:
                text += self.__writeDirValue(v, delimiter, stringFlag)
            elif type(v) is ListType:
                text += self.__writeListValue(v, delimiter, stringFlag)
            else:
                text += quotation + str(v) + quotation
            #
        #
        if stringFlag:
            return text
        #
        #text = text.replace("'False'", "false").replace("'True'", "true")
        text = text.replace(quotation + "False" + quotation, "false").replace(quotation + "True" + quotation, "true")
        text = text.replace(quotation + "false" + quotation, "false").replace(quotation + "true" + quotation, "true")
        return '[' + text + ']'

    def __getSelectionOption(self, SelectionInfo):
        """
        """
        SelectionHtml = ''
        for list in SelectionInfo:
            SelectionHtml += '<option value="' + list[0] + '"';
            if list[0] == '':
                SelectionHtml += ' selected';
            #
            SelectionHtml += '>' + list[1] + '</option>'
        #
        return SelectionHtml

    def __getSiteUserInfo(self):
        """
        """
        self._getUserInfoDict()
        if not self._statusDB:
            return []
        #
        return self._statusDB.getSiteUser(self._userInfo['site'])

def processPublicIDs(dataDict):
    if not dataDict:
        dataDict = {}
        dataDict['pdb_id'] = '-'
        dataDict['bmrb_id'] = '-'
        dataDict['emdb_id'] = '-'
    #
    for item in ( 'pdb_id', 'bmrb_id', 'emdb_id' ):
        if (not item in dataDict) or (not dataDict[item]) or (dataDict[item] == '?'):
            dataDict[item] = '-'
        #
    #
    return dataDict
