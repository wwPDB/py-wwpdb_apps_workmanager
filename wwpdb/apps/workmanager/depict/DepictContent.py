##
# File:  DepictContent.py
# Date:  30-Mar-2016
#
# Updates:
#  09-Dec-2024  zf   call _getPdbExtIdMap() method to get 'ext_pdb_id'
#
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
try:
    from urllib.parse import quote as u_quote
except ImportError:
    from urllib import quote as u_quote

from wwpdb.apps.workmanager.depict.DepictBase import DepictBase, processPublicIDs
from wwpdb.apps.workmanager.depict.ReadConFigFile import dumpPickleFile, loadPickleFile


class DepictContent(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(DepictContent, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        self.__returnMap = {}
        self._connectStatusDB()
        self._getUserInfoDict()
        self.__commun_tmplt = self._getPageTemplate('commun_tmplt')
        self.__commun_image_tmplt = self._getPageTemplate('commun_image_tmplt')
        self.__assign_annotator_tmplt = ''
        self.__AnnotatorSelection = ''
        self.__dataFieldMap = {}
        if 'table_data_field_binding' in self._conFigObj:
            self.__dataFieldMap = self._conFigObj['table_data_field_binding']
        #
        self.__sObj = self._reqObj.newSessionObj()
        self.__sessionId = self.__sObj.getId()
        self.__sessionPath = self.__sObj.getPath()

    def depictTableContent(self, index):
        """
        """
        self.__returnMap = {}
        tableContentMap = loadPickleFile(self.__sessionPath, 'TableContentMap.pkl')
        if index == 'all':
            for tableMap in tableContentMap.values():
                self._depictTableContent(tableMap)
            #
        elif index in tableContentMap:
            self._depictTableContent(tableContentMap[index])
        #
        return self.__returnMap

    def _depictTableContent(self, tableMap):
        """
        """
        if (not tableMap) or ('pkl' not in tableMap):
            return
        #
        if 'binding_function' in tableMap:
            if 'binding_class' in tableMap:
                self._processBindingClass(tableMap['binding_class'])
                classUtil = self._UtilClass[tableMap['binding_class']]
                _columnDef, contentResults = getattr(classUtil, '%s' % tableMap['binding_function'])()
            else:
                _columnDef, contentResults = getattr(self, '%s' % tableMap['binding_function'])()
            #
            dumpPickleFile(self.__sessionPath, tableMap['pkl'], contentResults)
            return
        #
        if ('sql' not in tableMap) or ('data-field' not in tableMap):
            return
        #
        count_map = self.__initializeStatusCount(tableMap)
        contentResults = []
        rows = self._statusDB.runSelectSQL(tableMap['sql'])
        if rows and ('sort_function' in tableMap):
            rows = getattr(self, '%s' % tableMap['sort_function'])(rows)
        #
        if rows:
            pdbExtIdMap = {}
            if ('pdb_ids' in tableMap['data-field']) or ('user_pdb_id' in tableMap['data-field']):
                pdbExtIdMap = self._getPdbExtIdMap(rows)
            #
            groupIdMap = {}
            idList = self.__getEntryIDList(rows, 'D_')
            if idList:
                return_list = self._statusDB.getGroupIds(depositionids=idList)
                if return_list:
                    for rD in return_list:
                        if ('group_id' in rD) and rD['group_id'] and ('dep_set_id' in rD) and rD['dep_set_id']:
                            groupIdMap[rD['dep_set_id']] = rD['group_id']
                        #
                    #
                #
                foundCombDateItem = False
                for field_item in tableMap['data-field']:
                    if field_item not in self.__dataFieldMap:
                        continue
                    #
                    value = self.__dataFieldMap[field_item]['value']
                    if value == 'deposition_release_dates':
                        foundCombDateItem = True
                        break
                    #
                #
                if foundCombDateItem:
                    self._connectContentDB()
                    releaseDateMap = self._contentDB.getReleaseDate("', '".join(sorted(set(idList))))
                    for dataD in rows:
                        dataD['deposition_release_dates'] = ''
                        if ('dep_set_id' not in dataD) or (not dataD['dep_set_id']):
                            continue
                        #
                        if ('dep_initial_deposition_date' in dataD) and dataD['dep_initial_deposition_date']:
                            dataD['deposition_release_dates'] = str(dataD['dep_initial_deposition_date']) + ' /<br /> '
                            if (dataD['dep_set_id'] in releaseDateMap) and releaseDateMap[dataD['dep_set_id']]:
                                dataD['deposition_release_dates'] += releaseDateMap[dataD['dep_set_id']]
                            else:
                                dataD['deposition_release_dates'] += 'n.a.'
                            #
                        elif (dataD['dep_set_id'] in releaseDateMap) and releaseDateMap[dataD['dep_set_id']]:
                            dataD['deposition_release_dates'] = 'n.a. /<br /> ' + releaseDateMap[dataD['dep_set_id']]
                        #
                    #
                #
            #
            annSelectMap = {}
            reminderSentMap = {}
            PIInfoMap = {}
            # if ('add_list' in tableMap['data-field']) or ('major_issue' in tableMap['data-field']) or \
            #        ('pi_name' in tableMap['data-field']) or ('country' in tableMap['data-field']) or \
            #        ('pi_name_only' in tableMap['data-field']) or ('pi_country_only' in tableMap['data-field']):

            if (  # pylint: disable=using-constant-test
                    x for x in tableMap['data-field'] if x in ('add_list',
                                                               'major_issue',
                                                               'pi_name',
                                                               'country',
                                                               'pi_name_only',
                                                               'pi_country_only',
                                                               'received_date')
            ):
                if idList and ('add_list' in tableMap['data-field']):
                    return_list = self._statusDB.getAnnoSelection(depositionids=idList)
                    annSelectMap = self.__convertListIntoMap(return_list)
                #
                if idList and (x for x in tableMap['data-field'] if x in ('major_issue',
                                                                          'received_date')
                               ):
                    return_list = self._statusDB.getRemindMessageTrack(depositionids=idList)
                    reminderSentMap = self.__convertListIntoMap(return_list)
                #
                if idList and (x for x in tableMap['data-field'] if x in ('pi_name',
                                                                          'country',
                                                                          'pi_name_only',
                                                                          'pi_country_only')
                               ):
                    PIInfoMap = self.__getPIInfo(idList)
                #
            #
            if 'assign_annotator' in tableMap['data-field']:
                self.__assign_annotator_tmplt = self._getPageTemplate('assign_annotator_tmplt')
                self.__AnnotatorSelection = self._getAnnotatorSelection()
            #
            order = 0
            for dataD in rows:
                dataD['display_ids'] = dataD['dep_set_id']
                dataD['group_info'] = ''
                if (dataD['dep_set_id'] in groupIdMap) and groupIdMap[dataD['dep_set_id']]:
                    dataD['display_ids'] = dataD['dep_set_id'] + '/' + groupIdMap[dataD['dep_set_id']]
                    dataD['group_info'] = '&group_id=' + groupIdMap[dataD['dep_set_id']]
                #
                if 'default_order' in tableMap['data-field']:
                    order_condition = ''
                    if 'order_condition' in tableMap:
                        order_condition = tableMap['order_condition']
                    #
                    dataD['default_order'] = self.__getOrder(order, len(rows), order_condition, dataD)
                #
                if count_map and ('dep_status_code' in dataD) and dataD['dep_status_code']:
                    status = str(dataD['dep_status_code'])
                    if status:
                        if status in count_map:
                            count_map[status] += 1
                        else:
                            count_map[status] = 1
                        #
                    #
                #
                dataD['locklabel'] = self.__processLockLabelForCommunication(dataD)
                if (dataD['dep_set_id'] in reminderSentMap) and reminderSentMap[dataD['dep_set_id']]:
                    dataD.update(reminderSentMap[dataD['dep_set_id']])
                #
                if (dataD['dep_set_id'] in PIInfoMap) and PIInfoMap[dataD['dep_set_id']]:
                    dataD.update(PIInfoMap[dataD['dep_set_id']])
                #
                if 'add_list' in tableMap['data-field']:
                    if (dataD['dep_set_id'] in annSelectMap) and annSelectMap[dataD['dep_set_id']]:
                        dataD['add_list'] = annSelectMap[dataD['dep_set_id']]['annotator_initials']
                    else:
                        dataD['add_list'] = 'Add'
                    #
                #
                dataD['base_url'] = ''
                if ('class_id' in dataD) and dataD['class_id']:
                    dataD['base_url'] = self._processBaseUrl(dataD['class_id'])
                #
                dataD['urlmethod'] = ''
                dataD['abbrv_method'] = ''
                if ('method' in dataD) and dataD['method']:
                    dataD['urlmethod'] = u_quote(dataD['method'])
                    if dataD['method'].upper() == 'X-RAY DIFFRACTION':
                        dataD['abbrv_method'] = 'X-RAY'
                    elif dataD['method'].upper() == 'NEUTRON DIFFRACTION':
                        dataD['abbrv_method'] = 'NEUTRON'
                    elif dataD['method'].upper() == 'FIBER DIFFRACTION' or dataD['method'].upper() == 'FIBRE DIFFRACTION':
                        dataD['abbrv_method'] = 'FIBER'
                    elif (
                            dataD['method'].upper() == 'CRYO-ELECTRON MICROSCOPY'
                            or dataD['method'].upper() == 'ELECTRON MICROSCOPY'
                            or dataD['method'].upper() == 'ELECTRON TOMOGRAPHY'
                    ):
                        dataD['abbrv_method'] = 'EM'
                    elif dataD['method'].upper() == 'ELECTRON CRYSTALLOGRAPHY':
                        dataD['abbrv_method'] = 'EL. CRYS.'
                    elif dataD['method'].upper() == 'SOLUTION NMR':
                        dataD['abbrv_method'] = 'NMR'
                    elif dataD['method'].upper() == 'SOLID-STATE NMR' or dataD['method'].upper() == 'SOLID STATE NMR':
                        dataD['abbrv_method'] = 'SS NMR'
                    else:
                        dataD['abbrv_method'] = dataD['method']
                    #
                #
                if ('pdb_ids' in tableMap['data-field']) or ('user_pdb_id' in tableMap['data-field']):
                    dataD = processPublicIDs(dataD, pdbExtIdMap)
                    if ('coor_status' in tableMap['data-field']) or ('author_status' in tableMap['data-field']):
                        dataD['comb_status_code'], dataD['comb_author_release_status_code'], titleEM, authorListEM = self.__processStatusCode(dataD)
                        if titleEM:
                            dataD['dep_title'] = titleEM
                        #
                        if authorListEM:
                            dataD['dep_author_list'] = authorListEM
                        #
                    #
                #
                self._dataInfo['data_for_all'] = [dataD]
                resultD = {}
                for field_item in tableMap['data-field']:
                    resultD[field_item] = ''
                    if field_item not in self.__dataFieldMap:
                        continue
                    #
                    value = self.__dataFieldMap[field_item]['value']
                    dtype = self.__dataFieldMap[field_item]['type']
                    if dtype == 'page_template':
                        resultD[field_item] = self.getPageText(page_id=value)
                    elif dtype == 'dataInfo':
                        if (value in dataD) and dataD[value]:
                            resultD[field_item] = str(dataD[value])
                        #
                    elif dtype == 'function':
                        resultD[field_item] = getattr(self, "%s" % value)(dataD)
                    #
                #
                contentResults.append(resultD)
                order += 1
            #
        #
        dumpPickleFile(self.__sessionPath, tableMap['pkl'], contentResults)
        #
        if 'entry_count' in tableMap:
            for t_type, ilist in tableMap['entry_count'].items():
                for item in ilist:
                    count = 0
                    if item == 'num_entries':
                        count = len(rows)
                    elif item in count_map:
                        count = count_map[item]
                    #
                    self.__returnMap[t_type + '_' + item + '_' + tableMap['tab_count_id']] = count
                #
            #
        #

    def _processWorkFlowStatus(self, dataD):
        """
        """
        if dataD['inst_status'] == 'waiting':
            return self.getPageText(page_id='workflow_waiting_status_tmplt')
        elif dataD['inst_status'] == 'closed(0)':
            return self.getPageText(page_id='workflow_close_status_tmplt')
        else:
            return self.getPageText(page_id='workflow_other_status_tmplt')

    def _processAssignSelection(self, dataD):
        """
        """
        myD = {}
        myD['dep_set_id'] = dataD['dep_set_id']
        myD['annotator_selection'] = self.__AnnotatorSelection
        return self.__assign_annotator_tmplt % myD

    def _processWorkFlowAction(self, dataD):
        """
        """
        if (dataD['dep_locking'].upper() == 'WFM') or (dataD['dep_status_code'].upper() == 'DEP'):
            return self.getPageText(page_id='workflow_lock_action_tmplt')
        elif dataD['inst_status'].lower() == 'init':
            return self.getPageText(page_id='workflow_init_action_tmplt')
        else:
            return self.getPageText(page_id='workflow_other_action_tmplt')
        #

    def _processAddList(self, dataD):
        """
        """
        if dataD['add_list'] == 'Add':
            return self.getPageText(page_id='add_list_tmplt')
        #
        return dataD['add_list']

    def _processCommunication(self, dataD):
        """
        """
        myD = {}
        myD['sessionid'] = self.__sessionId
        myD['initials'] = self._userInfo['initials']
        myD['dep_set_id'] = dataD['dep_set_id']
        myD['urlmethod'] = dataD['urlmethod']
        myD['locklabel'] = dataD['locklabel']
        #
        notify = dataD['dep_notify']
        imgD = {}
        imgD['image'] = 'wfm_comm.png'
        imgD['alt'] = 'Communication'
        if notify.find('N') != -1:
            imgD['image'] = 'wfm_new.png'
            imgD['alt'] = 'New Communication'
        elif notify.find('T') != -1:
            imgD['image'] = 'wfm_todo.png'
            imgD['alt'] = 'Communication to act on'
        #
        text = self.__commun_image_tmplt % imgD
        if notify.find('*') != -1:
            imgD['image'] = 'wfm_note.png'
            imgD['alt'] = 'Note'
            text += ' ' + self.__commun_image_tmplt % imgD
        #
        if notify.find('B') != -1:
            imgD['image'] = 'wfm_bmrb.png'
            imgD['alt'] = 'BMRB Message'
            text += ' ' + self.__commun_image_tmplt % imgD
        #
        if notify.find('A') != -1:
            imgD['image'] = 'wfm_approve.png'
            imgD['alt'] = 'Approve Message'
            text += ' ' + self.__commun_image_tmplt % imgD
        #
        myD['commun_image'] = text
        return self.__commun_tmplt % myD

    def _processAuxiliary(self, dataD):
        """
        """
        dep_notify = ''
        if 'dep_notify' in dataD:
            dep_notify = dataD['dep_notify']
        #
        dep_locking = ''
        if 'dep_locking' in dataD:
            dep_locking = dataD['dep_locking']
        #
        if dep_notify.find('R') != -1 and dep_locking == 'WFM':
            return 'background-red'
        elif dep_notify.find('R') != -1:
            return 'background-lightblue'
        elif dep_locking == 'WFM':
            return 'background-medpink'
        # If nothing else fall through
        # if dep_notify.find('A') != -1:
        #    return 'background-cyangreen'

        return ''

    def submit_group(self, rows):
        """ further process submitted group deposition
        """
        return self.__submit_group_filter(rows, True)

    def submit_group_search(self, rows):
        """ further process submitted group deposition
        """
        return self.__submit_group_filter(rows, False)

    def __submit_group_filter(self, rows, filter_by_annotator_flag):
        """
        """
        idList = self.__getEntryIDList(rows, 'G_')
        return_rows = self._statusDB.getEntryListForGroup(groupids=idList)
        groupIdMap = {}
        entryIdList = []
        for dataD in return_rows:
            if ('group_id' not in dataD) or (not dataD['group_id']) or ('dep_set_id' not in dataD) or (not dataD['dep_set_id']):
                continue
            #
            if dataD['group_id'] in groupIdMap:
                groupIdMap[dataD['group_id']].append(dataD['dep_set_id'])
            else:
                groupIdMap[dataD['group_id']] = [dataD['dep_set_id']]
                entryIdList.append(dataD['dep_set_id'])
            #
        #
        if not entryIdList:
            return []
        #
        info_rows = self._statusDB.getSimpleEntryInfo(depositionids=entryIdList)
        if not info_rows:
            return []
        #
        infoMap = {}
        for dataD in info_rows:
            infoMap[dataD['dep_set_id']] = dataD
        #
        groupInfoMap = {}
        for group_id, entry_ids in groupIdMap.items():
            if not entry_ids[0] in infoMap:
                continue
            #
            if (
                    ('annotator_initials' not in infoMap[entry_ids[0]]) or (not infoMap[entry_ids[0]]['annotator_initials'])
                    or (infoMap[entry_ids[0]]['annotator_initials'] != self._getUserInfo('initials'))) and filter_by_annotator_flag:
                continue
            #
            groupInfoMap[group_id] = {}
            groupInfoMap[group_id]['initial_deposition_date'] = ''
            if ('initial_deposition_date' in infoMap[entry_ids[0]]) and infoMap[entry_ids[0]]['initial_deposition_date']:
                groupInfoMap[group_id]['initial_deposition_date'] = infoMap[entry_ids[0]]['initial_deposition_date']
            #
            groupInfoMap[group_id]['status_code'] = self.__getGroupStatusCode(entry_ids)
        #
        group_rows = []
        for dataD in rows:
            if ('dep_set_id' not in dataD) or (not dataD['dep_set_id']) or (dataD['dep_set_id'] not in groupInfoMap):
                continue
            #
            for item in ('initial_deposition_date', 'status_code'):
                dataD[item] = groupInfoMap[dataD['dep_set_id']][item]
            #
            group_rows.append(dataD)
        #
        return group_rows

    def unsubmit_group(self, rows):
        """ further process un-submitted group deposition
        """
        nRows = []
        tRows = []
        cRows = []
        rRows = []
        for dataD in rows:
            if ('dep_notify' in dataD) and dataD['dep_notify']:
                if dataD['dep_notify'].find('N') != -1:
                    nRows.append(dataD)
                elif dataD['dep_notify'].find('T') != -1:
                    tRows.append(dataD)
                else:
                    cRows.append(dataD)
                #
            else:
                rRows.append(dataD)
            #
        #
        if tRows:
            nRows.extend(tRows)
        #
        if cRows:
            nRows.extend(cRows)
        #
        if rRows:
            nRows.extend(rRows)
        #
        return nRows

    def __initializeStatusCount(self, tableMap):
        """
        """
        count_map = {}
        if 'entry_count' in tableMap:
            for itemList in tableMap['entry_count'].values():
                for item in itemList:
                    if item == 'num_entries':
                        continue
                    #
                    count_map[item] = 0
                #
            #
        #
        return count_map

    def __getEntryIDList(self, rows, prefix):
        """
        """
        idlist = []
        for dataD in rows:
            if ('dep_set_id' in dataD) and dataD['dep_set_id'] and dataD['dep_set_id'].startswith(prefix):
                idlist.append(dataD['dep_set_id'])
            #
        #
        return idlist

    def __convertListIntoMap(self, rList):
        """
        """
        Map = {}
        if not rList:
            return Map
        #
        for dataD in rList:
            Map[dataD['dep_set_id']] = dataD
        #
        return Map

    def __getPIInfo(self, rList):
        """
        """
        Map = self.__getPIInfoFromCotentDB(rList)
        foundMissing = False
        for depId in rList:
            if depId not in Map:
                foundMissing = True
                break
            #
        #
        if not foundMissing:
            return Map
        #
        Map1 = self.__getPIInfoFromStatusDB(rList)
        for depId in rList:
            if depId in Map:
                continue
            #
            if depId in Map1:
                Map[depId] = Map1[depId]
            else:
                validContactAuthor = self._statusDB.ValidContactAuthor(depId)
                if validContactAuthor:
                    tmpMap = {}
                    if ('last_name' in validContactAuthor) and validContactAuthor['last_name']:
                        tmpMap['pi_name'] = validContactAuthor['last_name']
                    #
                    if ('country' in validContactAuthor) and validContactAuthor['country']:
                        tmpMap['country'] = validContactAuthor['country']
                    #
                    if tmpMap:
                        Map[depId] = tmpMap
                    #
                #
            #
        #
        return Map

    def __getPIInfoFromCotentDB(self, rList):
        """
        """
        self._connectContentDB()
        return self.__processPIInfo(self._contentDB.ContactAuthorPI(rList), ['name_first', 'name_mi', 'name_last'])

    def __getPIInfoFromStatusDB(self, rList):
        """
        """
        return self.__processPIInfo(self._statusDB.ContactAuthorPI(rList), ['last_name'])

    def __processPIInfo(self, rows, name_items):
        """
        """
        Map = {}
        if not rows:
            return Map
        #
        for dataD in rows:
            dep_id = ''
            if ('id' in dataD) and dataD['id']:
                dep_id = str(dataD['id'])
            #
            if not dep_id:
                continue
            #
            country = ''
            if ('country' in dataD) and dataD['country']:
                country = str(dataD['country'])
            #
            if not country:
                continue
            #
            pi_name = ''
            for item in name_items:
                if (item not in dataD) or (not dataD[item]):
                    continue
                #
                if pi_name:
                    pi_name += ' '
                #
                pi_name += str(dataD[item])
            #
            if not pi_name:
                continue
            #
            if dep_id in Map:
                Map[dep_id]['pi_name'] += ", <br/>" + pi_name
                Map[dep_id]['country'] += ", <br/>" + country
                Map[dep_id]['pi_name_only'] += ", <br/>" + pi_name
                Map[dep_id]['pi_country_only'] += ", <br/>" + country
            else:
                Map[dep_id] = {'pi_name': pi_name, 'country': country, 'pi_name_only': pi_name, 'pi_country_only': country}
            #
        #
        return Map

    def __getOrder(self, order, num_rows, order_condition, dataD):
        """
        """
        if not order_condition:
            return str(order)
        #
        condition_list = order_condition.split(':')
        value_list = condition_list[1].split(',')
        num = len(value_list) + 1
        if (condition_list[0] in dataD) and dataD[condition_list[0]]:
            count = 1
            for value in value_list:
                if condition_list[0] == 'dep_notify':
                    if dataD[condition_list[0]].find(value) != -1:
                        num = count
                        break
                    #
                elif dataD[condition_list[0]] == value:
                    num = count
                    break
                #
                count += 1
            #
        #
        return str(num * num_rows + order)

    def __processLockLabelForCommunication(self, dataDict):
        """
        """
        # Determine if unlock from communication is allowed when invoked from WFM
        # dep_status_code and dep_locking must be present.
        # Must be unlocked
        # Must not be DEP, OBS, or WDRN status (author initiated post_relase allows REL if pdb_id present (i.e. not map onlu)
        if ('dep_status_code' not in dataDict) or ('dep_locking' not in dataDict) or (str(dataDict['dep_locking']).upper() == 'WFM') or \
           (str(dataDict['dep_status_code']).upper() in ('DEP', 'OBS', 'WDRN')):
            return ''

        # Check for map only
        if str(dataDict['dep_status_code']).upper() == 'REL' and ('pdb_id' not in dataDict or len(dataDict['pdb_id']) < 2):
            return ""
        return '&allowunlock=yes'

    def __processStatusCode(self, dataDict):
        """
        """
        statusCode = ''
        authorReleaseStatusCode = ''
        titleEM = ''
        authorListEM = ''
        baseStatusCode = ''
        if 'dep_status_code' in dataDict and dataDict['dep_status_code']:
            baseStatusCode = dataDict['dep_status_code']
            if 'dep_post_rel_status' in dataDict and dataDict['dep_post_rel_status']:
                baseStatusCode = dataDict['dep_post_rel_status'] + '(' + baseStatusCode + ')'

        if dataDict['emdb_id'] != '-':
            # EMDB ID
            if dataDict['pdb_id'] != '-':
                # PDB ID present
                if ('dep_status_code' in dataDict) and dataDict['dep_status_code'] and ('dep_status_code_emdb' in dataDict) and dataDict['dep_status_code_emdb']:
                    statusCode = baseStatusCode + '/' + dataDict['dep_status_code_emdb']
                else:
                    statusCode = baseStatusCode
                #
                if ('dep_author_release_status_code' in dataDict) and dataDict['dep_author_release_status_code'] and \
                   ('dep_author_release_status_code_emdb' in dataDict) and dataDict['dep_author_release_status_code_emdb']:
                    authorReleaseStatusCode = dataDict['dep_author_release_status_code'] + '/' + dataDict['dep_author_release_status_code_emdb']
                elif ('dep_author_release_status_code' in dataDict) and dataDict['dep_author_release_status_code']:
                    authorReleaseStatusCode = dataDict['dep_author_release_status_code']
                #
            else:
                # Map only
                if ('dep_status_code_emdb' in dataDict) and dataDict['dep_status_code_emdb']:
                    statusCode = dataDict['dep_status_code_emdb']
                #
                if ('dep_author_release_status_code_emdb' in dataDict) and dataDict['dep_author_release_status_code_emdb']:
                    authorReleaseStatusCode = dataDict['dep_author_release_status_code_emdb']
                #
                if ('title_emdb' in dataDict) and dataDict['title_emdb']:
                    titleEM = dataDict['title_emdb']
                #
                if ('author_list_emdb' in dataDict) and dataDict['author_list_emdb']:
                    authorListEM = dataDict['author_list_emdb']
                #
            #
        else:
            # No emdb id
            statusCode = baseStatusCode
            #
            if ('dep_author_release_status_code' in dataDict) and dataDict['dep_author_release_status_code']:
                authorReleaseStatusCode = dataDict['dep_author_release_status_code']
            #
        #
        return statusCode, authorReleaseStatusCode, titleEM, authorListEM

    def __getGroupStatusCode(self, entryIdList):
        status_code = 'unknown'
        count = 0
        info_rows = self._statusDB.getSimpleEntryInfo(depositionids=entryIdList)
        if not info_rows:
            return status_code
        #
        statusMap = {}
        for dataD in info_rows:
            if ('status_code' not in dataD) or (not dataD['status_code']):
                continue
            #
            code = str(dataD['status_code']).strip().upper()
            if code in statusMap:
                statusMap[code] += 1
            else:
                statusMap[code] = 1
            #
        #
        for code, val in statusMap.items():
            if val > count:
                count = val
                status_code = code
            #
        #
        return status_code
