##
# File:  StatusDbApi.py
# Date:  04-May-2015
# Updates:
##
"""
Providing addintaional APIs for WFE to get info from status database.

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


import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.wf.dbapi.WFEtime import getTimeNow
from wwpdb.apps.workmanager.db_access.DbApiUtil import DbApiUtil


class StatusDbApi(object):
    __schemaMap = { "AUTENTICATE" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.user_name = '%s' and u.password = '%s' and u.active = 0",
                    "SELECT_USER" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.user_name = '%s'",
             "SELECT_ACTIVE_USER" : "select user_name, first_name, last_name, initials from da_users as dau, da_group as dag where " +
                                    "dau.da_group_id=dag.da_group_id and code='ANN' and site in ('PDBj', 'RCSB', 'PDBC') " +
                                    "and initials not in ( 'JY', 'JW') and active = 0",
              "SELECT_USER_EMAIL" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.email = '%s'",
            "SELECT_USER_INITIAL" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.initials = '%s'",
                    "UPDATE_USER" : "update da_users set password = '%s', email = '%s', first_name = '%s', last_name = '%s' where " +
                                    "user_name = '%s'",
                   "SELECT_SITES" : "select g.code, g.group_name, g.site, g.da_group_id, g.main_page from da_group as g",
                "SELECT_SITE_ANN" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.active = 0 and g.code = '%s' and g.site = '%s'",
              "SELECT_GROUP_USER" : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = " +
                                    "g.da_group_id and u.active = 0 and u.da_group_id = '%s'",
              "SELECT_SITE_GROUP" : "select code, group_name, site, da_group_id group_id from da_group where site = '%s'", 
    "SELECT_SITE_GROUP_WITH_CODE" : "select code, group_name, site, da_group_id group_id from da_group where site = '%s' and code = '%s'",
              "SELECT_SITE_USER"  : "select u.user_name, u.password, u.da_group_id group_id, u.email, u.initials, u.first_name, u.last_name, " +
                                    "u.active, g.code, g.group_name, g.site from da_users as u, da_group as g where u.da_group_id = g.da_group_id " +
                                    "and g.site = '%s' order by u.active, g.code, u.initials",
              "SERVER_MONITORING" : "select hostname, status_timestamp from engine_monitoring",
        "SELECT_DEPOSITION_BY_ID" : "select depPW as deppw, pdb_id, bmrb_id, emdb_id, title from deposition where dep_set_id = '%s'",
          "SELECT_TIMESTAMP_INFO" : "select ordinal, mtime, event, info1, info2 from timestamp where dep_set_id = '%s' order by ordinal",
   "SELECT_SINGLE_ANNO_SELECTION" : "select dep_set_id, annotator_initials from anno_selection where dep_set_id = '%s'",
 "SELECT_MULTIPLE_ANNO_SELECTION" : "select dep_set_id, annotator_initials from anno_selection where dep_set_id in ( '%s' )",
                "GET_CLASS_BY_ID" : "select wf_class_id, wf_class_name, title, author, version, class_file from wf_class_dict where " +
                                    "wf_class_id = '%s'",
          "DELETE_ANNO_SELECTION" : "delete from anno_selection where dep_set_id = '%s'",
          "INSERT_ANNO_SELECTION" : "insert into anno_selection (dep_set_id, annotator_initials) values ( '%s', '%s' )",
#                "UP_INST_STATUS" : "update wf_instance set inst_status = '%s', owner = '%s' where dep_set_id = '%s' and wf_inst_id = '%s' " +
#                                   " and wf_class_id = '%s'",
    "SELECT_SINGLE_MESSAGE_TRACK" : "select dep_set_id, major_issue, last_reminder_sent_date, last_validation_sent_date, last_message_sent_date, " +
                                    "last_message_received_date from remind_message_track where dep_set_id = '%s'",
  "SELECT_MULTIPLE_MESSAGE_TRACK" : "select dep_set_id, major_issue, last_reminder_sent_date, last_validation_sent_date, last_message_sent_date, " +
                                    "last_message_received_date from remind_message_track where dep_set_id in ( '%s' )",
           "DELETE_MESSAGE_TRACK" : "delete from remind_message_track where dep_set_id = '%s'",
          "UPDATE_ANN_DEPOSITION" : "update deposition set annotator_initials  = '%s' where dep_set_id = '%s'",
           "UPDATE_ANN_LAST_INST" : "update dep_last_instance set annotator_initials  = '%s' where dep_set_id = '%s'",
           "SELECT_LAST_INSTANCE" : "select class_id as wf_class_id, inst_id as wf_inst_id, inst_status, dep_set_id, dep_exp_method, pdb_id, dep_bmrb_id as " +
                                    "bmrb_id, dep_emdb_id as emdb_id, dep_status_code, dep_status_code_exp, dep_author_release_status_code, " +
                                    "dep_initial_deposition_date, annotator_initials, dep_notify, dep_locking, dep_title, dep_author_list, dep_post_rel_status from " +
                                    "dep_last_instance where dep_set_id = '%s'", 
        "SELECT_WF_LAST_INSTANCE" : "select ordinal, wf_inst_id, wf_class_id, dep_set_id, owner, inst_status, status_timestamp from wf_instance " +
                                    "where dep_set_id = '%s' and wf_class_id = '%s' order by status_timestamp desc limit 1",
         "SELECT_WF_ALL_INSTANCE" : "select wf_inst_id, wf_class_id, dep_set_id, inst_status, status_timestamp from wf_instance " +
                                    "where dep_set_id = '%s' and wf_class_id not in ( 'Annotate', 'depUpload' ) order by wf_inst_id",
           "SELECT_COMMUNICATION" : "select ordinal, sender, receiver, dep_set_id, wf_class_id, wf_inst_id, wf_class_file, command, status, actual_timestamp, " +
                                    "parent_dep_set_id, parent_wf_class_id, parent_wf_inst_id, data_version from communication where " +
                                    "parent_dep_set_id = '%s' order by actual_timestamp desc limit 1",
           "SELECT_DEP_WF_STATUS" : "select inst_status from dep_instance where dep_set_id = '%s' and inst_id = '%s' and class_id = '%s'",
                  "GET_REAL_FLOW" : "select wf_task_id, task_status, status_timestamp, task_type from wf_task where dep_set_id = '%s' and wf_inst_id = '%s' " +
                                    "and wf_class_id = '%s' order by status_timestamp asc",
           "CONTACT_AUTHOR_PI"    : "select dep_set_id as id, email, last_name, role, country from user_data where dep_set_id in ( '%s' ) and role = '%s'",
           "CHECK_TABLE_EXIST"    : "select distinct table_name from  information_schema.tables where table_schema = '%s' and table_name = '%s'",
                          "COUNT" : "select count(*) from %s",
                 "GET_ENTRY_LIST" : "select dep_set_id,pdb_id,emdb_id,bmrb_id from deposition where %s",
      "GET_ENTRY_LIST_FROM_GROUP" : "select group_id, dep_set_id from group_deposition_information where group_id in ( '%s' ) order by dep_set_id",
                "SELECT_GROUP_ID" : "select dep_set_id, group_id from group_deposition_information where dep_set_id in ( '%s' )",
                 "GET_ENTRY_INFO" : "select dep_set_id, initial_deposition_date, annotator_initials, status_code from deposition where dep_set_id in ( '%s' ) " +
                                    "order by dep_set_id",
                   }
    #
    __comm_items = ['sender', 'receiver', 'dep_set_id', 'wf_class_id', 'wf_inst_id', 'wf_class_file', 'command', 'status', 'actual_timestamp',
                    'parent_dep_set_id', 'parent_wf_class_id', 'parent_wf_inst_id', 'data_version']
    """
    """
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        """
        """
        self.__lfh = log
        self.__verbose = verbose
        self.__siteId = siteId
        self.__cI = ConfigInfo(self.__siteId)
        self.__dbServer = self.__cI.get("SITE_DB_SERVER")
        self.__dbHost = self.__cI.get("SITE_DB_HOST_NAME")
        self.__dbName = self.__cI.get("SITE_DB_DATABASE_NAME")
        self.__dbUser = self.__cI.get("SITE_DB_USER_NAME")
        self.__dbPw = self.__cI.get("SITE_DB_PASSWORD")
        self.__dbSocket = self.__cI.get("SITE_DB_SOCKET")
        self.__dbPort = int(self.__cI.get("SITE_DB_PORT_NUMBER"))
        #
        self.__dbApi = DbApiUtil(dbServer=self.__dbServer, dbHost=self.__dbHost, dbName=self.__dbName, dbUser=self.__dbUser, dbPw=self.__dbPw,
                                 dbSocket=self.__dbSocket, dbPort=self.__dbPort, verbose=self.__verbose, log=self.__lfh)
        self.__dbApi.setSchemaMap(self.__schemaMap)

    def __getDataDir(self, key, parameter, idx):
        dlist = self.__dbApi.selectData(key=key, parameter=parameter)
        if dlist:
            return dlist[idx]
        #
        return None

    def Autenticate(self, username=None, password=None):
        if not username or not password:
            return None
        #
        return self.__getDataDir("AUTENTICATE", (username, password), 0)

    def getUserByName(self, username=None):
        if not username:
            return None
        #
        return self.__getDataDir("SELECT_USER", (username), 0)

    def getActiveAnnoList(self):
        return self.__dbApi.selectData(key="SELECT_ACTIVE_USER", parameter=())

    def getUserByEmail(self, email=None):
        if not email:
            return None
        #
        return self.__getDataDir("SELECT_USER_EMAIL", (email), 0)

    def getUserByInitial(self, initial=None):
        if not initial:
            return None
        #
        return self.__getDataDir("SELECT_USER_INITIAL", (initial), 0)

    def updateUser(self, password=None, email=None, first_name=None, last_name=None, user_name=None):
        if not password or not email or not first_name or not last_name or not user_name:
            return 'Update user information failed.'
        #
        sql = self.__schemaMap['UPDATE_USER'] % (password, email, first_name, last_name, user_name)
        ret = self.__dbApi.runUpdateSQL(sql)
        if ret != 'OK':
            return 'Update user information failed.'
        else:
            return 'User Information Updated.'
        #

    def getAnnUser(self, site=None):
        if not site:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_SITE_ANN", parameter=('ANN', site))

    def getAnnLeader(self, site=None):
        if not site:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_SITE_ANN", parameter=('LANN', site))

    def getGroupUser(self, da_group_id=None):
        if not da_group_id:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_GROUP_USER", parameter=(da_group_id))

    def getSites(self):
        """Returns list of sites in WFM user table"""
        return self.__dbApi.selectData(key="SELECT_SITES", parameter=())

    def getSiteGroup(self, site=None):
        if not site:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_SITE_GROUP", parameter=(site))

    def getSiteGroupWithCode(self, site=None, code=None):
        if not site or not code:
            return None
        #
        return self.__getDataDir("SELECT_SITE_GROUP_WITH_CODE", (site, code), 0)

    def getSiteUser(self, site=None):
        if not site:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_SITE_USER", parameter=(site))

    def getDepInfo(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__getDataDir("SELECT_DEPOSITION_BY_ID", (depositionid), 0)

    def getServerInfo(self):
        return self.__dbApi.selectData(key="SERVER_MONITORING", parameter=())

    def getTimeStampInfo(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_TIMESTAMP_INFO", parameter=(depositionid))

    def getLastInstance(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__getDataDir("SELECT_LAST_INSTANCE", (depositionid), 0)

    def runSelectSQL(self, sql):
        return self.__dbApi.runSelectSQL(sql)

    def killWorkFlow(self, depositionid=None):
        if not depositionid:
            return 'No deposition ID defined.'
        #
        cloumns = {}
        cloumns['command'] = 'killWF'
        cloumns['actual_timestamp'] = str(getTimeNow())
        cloumns['receiver'] = 'WFE'
        cloumns['status'] = 'PENDING'
        set_command = self.__getSetCommand(cloumns)
        sql = 'update communication set ' + set_command + " where dep_set_id = '" + str(depositionid) + "'"
        ret = self.__dbApi.runUpdateSQL(sql)
        if ret != 'OK':
            return 'Failed to mark ' + depositionid + ' for process kill'
        else:
            return 'OK'
        #

    def addToMyList(self, depositionid=None, initial=None):
        if not depositionid or not initial:
            return
        #
        if self.__dbApi.selectData(key="SELECT_SINGLE_ANNO_SELECTION", parameter=(depositionid)):
            return
        #
        self.__dbApi.runUpdateSQLwithKey(key="INSERT_ANNO_SELECTION", parameter=(depositionid, initial))

    def removeFromMyList(self, depositionid=None):
        if not depositionid:
            return
        #
        if not self.__dbApi.selectData(key="SELECT_SINGLE_ANNO_SELECTION", parameter=(depositionid)):
            return
        #
        self.__dbApi.runUpdateSQLwithKey(key="DELETE_ANNO_SELECTION", parameter=(depositionid))

    def getAnnoSelection(self, depositionids=None):
        return self.__getSelectionResult(depositionids, 'SELECT_MULTIPLE_ANNO_SELECTION')

    def getWfClassByID(self, classID=None):
        if not classID:
            return None
        #
        return self.__getDataDir("GET_CLASS_BY_ID", (classID), 0)

    def getSimpleEntryInfo(self, depositionids=None):
        return self.__getSelectionResult(depositionids, 'GET_ENTRY_INFO')

    #   def updateInstStatus(self, status=None, owner=None, depositionid=None, instanceid=None, classID=None):
    #       if not status or not owner or not depositionid or not instanceid or not classID:
    #           return 'Start Annotate workflow failed.'
    #       #
    #       sql = self.__schemaMap['UP_INST_STATUS'] % ( status, owner, depositionid, instanceid, classID)
    #       ret = self.__dbApi.runUpdateSQL(sql)
    #       if ret != 'OK':
    #           return 'Start Annotate workflow failed.'
    #       else:
    #           return 'OK'
    #       #

    def getRemindMessageTrack(self, depositionids=None):
        return self.__getSelectionResult(depositionids, 'SELECT_MULTIPLE_MESSAGE_TRACK')

    def insertRemindMessageTrack(self, depositionid=None, dataMap=None):
        """
        """
        if not depositionid or not dataMap:
            return
        #
        if self.__dbApi.selectData(key="SELECT_SINGLE_MESSAGE_TRACK", parameter=(depositionid)):
            self.__dbApi.runUpdateSQLwithKey(key="DELETE_MESSAGE_TRACK", parameter=(depositionid))
        #
        key = []
        values = []
        key.append('dep_set_id')
        values.append("'" + depositionid + "'")
        for k, v in dataMap.items():
            key.append(k)
            values.append("'" + v + "'")
        #
        sql = 'insert into remind_message_track ( ' + ', '.join(key) + ' ) values ( ' + ', '.join(values) + ' ) '
        self.__dbApi.runUpdateSQL(sql)

    def updateAnnotatorAssignment(self, assignList=None):
        """
        """
        if not assignList:
            return
        #
        for alist in assignList:
            sql = self.__schemaMap['UPDATE_ANN_DEPOSITION'] % (alist[1], alist[0])
            _ret = self.__dbApi.runUpdateSQL(sql)  # noqa: F841
            # if rows < 1:
            #   catch error
            sql = self.__schemaMap['UPDATE_ANN_LAST_INST'] % (alist[1], alist[0])
            _ret = self.__dbApi.runUpdateSQL(sql)  # noqa: F841
            # if rows < 1:
            #   catch error
        #

    def getLastWFInstance(self, depositionid=None, classid=None):
        if not depositionid or not classid:
            return None
        #
        return self.__getDataDir("SELECT_WF_LAST_INSTANCE", (depositionid, classid), -1)

    def getAllWFInstances(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__dbApi.selectData(key="SELECT_WF_ALL_INSTANCE", parameter=(depositionid))

    def getLastWFCommunication(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__getDataDir("SELECT_COMMUNICATION", (depositionid), -1)

    def getDepositionStatus(self, depositionid=None, instid=None, classid=None):
        status = 'unkown'
        if not depositionid or not classid or not instid:
            return status
        #
        data = self.__getDataDir("SELECT_DEP_WF_STATUS", (depositionid, instid, classid), 0)
        if data:
            status = data['inst_status'].upper()
        #
        return status

    def getRealFlow(self, depositionid=None, instid=None, classid=None):
        if not depositionid or not classid or not instid:
            return None
        #
        return self.__dbApi.selectData(key="GET_REAL_FLOW", parameter=(depositionid, instid, classid))

    def ContactAuthorPI(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__dbApi.selectData(key="CONTACT_AUTHOR_PI", parameter=("', '".join(depositionid), 'principa'))

    def ValidContactAuthor(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__getDataDir("CONTACT_AUTHOR_PI", (depositionid, 'valid'), 0)

    def getCommandStatus(self, depositionid=None):
        status = 'unkown'
        if not depositionid:
            return status
        #
        data = self.getLastWFCommunication(depositionid=depositionid)
        if data and ('status' in data):
            status = data['status'].upper()
        #
        return status

    def insertCommunicationCommand(self, depositionid=None, instid=None, classid=None, command=None, classname=None, dataversion=None):
        if not depositionid or not classid or not command or not classname:
            return 'Start Annotate workflow failed.'
        #
        myD = {}
        myD['sender'] = 'WFM'
        myD['receiver'] = 'WFE'
        myD['dep_set_id'] = depositionid
        myD['wf_class_file'] = classname
        myD['command'] = command
        myD['status'] = 'pending'
        myD['parent_dep_set_id'] = depositionid
        myD['parent_wf_class_id'] = classid
        if instid:
            myD['parent_wf_inst_id'] = instid
        #
        if dataversion:
            myD['data_version'] = dataversion
        #
        sql = ''
        comm = self.getLastWFCommunication(depositionid=depositionid)
        if comm:
            set_comm = ''
            for item in self.__comm_items:
                if set_comm:
                    set_comm += ', '
                #
                if item in myD:
                    set_comm += item + " = '" + str(myD[item]) + "'"
                else:
                    set_comm += item + ' = Null'
                #
            #
            if set_comm:
                sql = 'update communication set ' + set_comm + " where ordinal = '" + str(comm['ordinal']) + "'"
            #
        else:
            items = ''
            values = ''
            for item in self.__comm_items:
                if item not in myD:
                    continue
                #
                if items:
                    items += ', '
                    values += ', '
                #
                items += item
                values += "'" + str(myD[item]) + "'"
            #
            if items and values:
                sql = 'insert communication ( ' + items + ' ) values ( ' + values + ' )'
            #
        #
        if not sql:
            return 'Start Annotate workflow failed.'
        #
        ret = self.__dbApi.runUpdateSQL(sql)
        if ret != 'OK':
            return 'Start Annotate workflow failed.'
        else:
            return 'OK'
        #

    def runUpdate(self, table=None, where=None, data=None):
        return self.__dbApi.runUpdate(table=table, where=where, data=data)

    def isTableExist(self, table=None):
        if not table:
            return False
        #
        ret_list = self.__dbApi.selectData(key="CHECK_TABLE_EXIST", parameter=(self.__dbName, table))
        if len(ret_list) > 0:
            return True
        #
        return False

    def isTableValid(self, table=None):
        if not table:
            return False
        #
        if self.isTableExist(table=table):
            rdir = self.__getDataDir("COUNT", (table), 0)
            if rdir['count(*)'] > 0:
                return True
            #
        #
        return False

    def getEntryListForGroup(self, groupids=None):
        if not groupids:
            return None
        #
        # return self.__dbApi.selectData(key="GET_ENTRY_LIST_FROM_GROUP", parameter=(groupid))
        return self.__getSelectionResult(groupids, 'GET_ENTRY_LIST_FROM_GROUP')

    def getGroupIds(self, depositionids=None):
        return self.__getSelectionResult(depositionids, 'SELECT_GROUP_ID')

    def __getSetCommand(self, data):
        command = ''
        for k, v in data.items():
            if command:
                command += ', '
            #
            command += k + " = '" + v + "'"
        #
        return command

    def __getSelectionResult(self, depositionids, schema_key):
        if not depositionids:
            return None
        #
        ids = "', '".join(depositionids)
        sql = self.__schemaMap[schema_key] % (ids)
        #
        return self.__dbApi.runSelectSQL(sql)

    def getDistinctAnnotatorInitials(self):
        aiList = []
        rows = self.__dbApi.runSelectSQL('select distinct upper(annotator_initials) from deposition')
        for row in rows:
            if ('upper(annotator_initials)' in row) and row['upper(annotator_initials)']:
                aiList.append(row['upper(annotator_initials)'])
            #
        #
        return aiList

    def getActiveAnnotatorInitials(self):
        aaiList = []
        rows = self.__dbApi.runSelectSQL('select upper(initials) from da_users where active = 0')
        for row in rows:
            if ('upper(initials)' in row) and row['upper(initials)']:
                aaiList.append(row['upper(initials)'])
            #
        #
        return aaiList

    def getRetiredAnnotatorInitials(self):
        rtList = []
        distinctList = self.getDistinctAnnotatorInitials()
        activeList = self.getActiveAnnotatorInitials()
        for ai in distinctList:
            if (ai == 'UNKNOWN') or (ai == 'UNASSIGN') or (ai in activeList):
                continue
            #
            rtList.append(ai)
        #
        return rtList

    def getEntryIdListFromInputIdString(self, entry_id_string):
        group_ids = []
        id_type_map = {}
        error_message = ''
        #
        input_id_list = entry_id_string.upper().replace(',', ' ').replace('\n', ' ').replace('\t', ' ').split(' ')
        for input_id in input_id_list:
            if not input_id:
                continue
            #
            id_type = ''
            if input_id[:2] == 'D_':
                id_type = 'dep_set_id'
            elif input_id[:2] == 'G_':
                id_type = 'group_id'
            elif (input_id[:4] == "EMD-") or (input_id[:5] == "EMDB-"):
                id_type = 'emdb_id'
            elif len(input_id) == 4:
                id_type = 'pdb_id'
            elif len(input_id) == 5:
                id_type = 'bmrb_id'
            elif (len(input_id) == 12) and input_id.lower().startswith('pdb_'):
                id_type = 'pdb_id'
            #
            if not id_type:
                if error_message:
                    error_message += "\n"
                #
                error_message += "'" + input_id + "' is not a valid ID."
                continue
            #
            if id_type == 'group_id':
                group_ids.append(input_id)
            else:
                if id_type in id_type_map:
                    id_type_map[id_type].append(input_id)
                else:
                    id_type_map[id_type] = [input_id]
                #
                if input_id.lower().startswith('pdb_0000') and (id_type == 'pdb_id'):
                    short_pdb_id = input_id[8:]
                    #
                    if id_type in id_type_map:
                        id_type_map[id_type].append(short_pdb_id)
                    else:
                        id_type_map[id_type] = [short_pdb_id]
                    #
                #
            #
        #
        if (not id_type_map) and (not group_ids):
            if not error_message:
                error_message = "No Entry IDs defined."
            #
            return error_message, []
        #
        group_error_message, entryList = self.__getDepIDFromGroupID(group_ids)
        if group_error_message:
            if error_message:
                error_message += "\n"
            #
            error_message += group_error_message
        #
        entry_error_message, other_entry_list = self.__getDepIDFromFromIdTypeMap(id_type_map)
        if entry_error_message:
            if error_message:
                error_message += "\n"
            #
            error_message += entry_error_message
        #
        if other_entry_list:
            entryList.extend(other_entry_list)
            entryList = sorted(set(entryList))
        #
        return error_message, entryList

    def __getDepIDFromGroupID(self, group_ids):
        if not group_ids:
            return '', []
        #
        group_ids = sorted(set(group_ids))
        return self.__processGetEntryListResult(self.getEntryListForGroup(groupids=group_ids), group_ids, ['group_id'])

    def __getDepIDFromFromIdTypeMap(self, id_type_map):
        if not id_type_map:
            return '', []
        #
        parameter = ''
        input_id_list = []
        id_type_list = []
        for id_type in ('dep_set_id', 'pdb_id', 'bmrb_id', 'emdb_id'):
            if (id_type not in id_type_map) or (not id_type_map[id_type]):
                continue
            #
            id_type_map[id_type] = sorted(set(id_type_map[id_type]))
            input_id_list.extend(id_type_map[id_type])
            id_type_list.append(id_type)
            if parameter:
                parameter += " or "
            #
            parameter += " " + id_type + " in ( '" + "', '".join(id_type_map[id_type]) + "' ) "
        #
        if not parameter:
            return '', []
        #
        return self.__processGetEntryListResult(self.__dbApi.selectData(key='GET_ENTRY_LIST', parameter=(parameter)), input_id_list, id_type_list)

    def __processGetEntryListResult(self, return_list, input_id_list, id_type_list):
        return_id_list = []
        found_id_map = {}
        if return_list:
            for myD in return_list:
                if ('dep_set_id' in myD) and myD['dep_set_id']:
                    return_id_list.append(myD['dep_set_id'].upper())
                #
                for id_type in id_type_list:
                    if (id_type in myD) and myD[id_type]:
                        found_id_map[myD[id_type].upper()] = 'yes'
                    #
                #
            #
        #
        error_message = ''
        for input_id in input_id_list:
            if input_id in found_id_map:
                continue
            #
            if error_message:
                error_message += "\n"
            #
            error_message += "'" + input_id + "' is not a valid ID."
        #
        return error_message, return_id_list

    def deleteSite(self, site):
        """Deletes a site by retrieving the group id and then deleting users and group"""

        status = 'OK'
        sitegr = self.getSiteGroup(site)
        for s in sitegr:
            groupid = s['group_id']

            sql = "delete from da_users where da_group_id = '{}'".format(groupid)
            ret = self.__dbApi.runUpdateSQL(sql)

            sql = "delete from da_group where da_group_id = '{}'".format(groupid)
            ret = self.__dbApi.runUpdateSQL(sql)
            if ret != 'OK':
                status = ret

        return status

    def addSite(self, site, lead, email, first, last):  # pylint: disable=unused-argument
        # First determine new group
        sites = self.getSites()
        maxgroup = 0
        status = 'OK'
        for s in sites:
            if s['site'].lower() == site.lower():
                status = 'Site already exists'
                return status
            maxgroup = max(maxgroup, s['da_group_id'])

        for code in ['LANN', 'ANN']:
            maxgroup += 1
            if code == 'LANN':
                group_name = "{} - Lead Annotator".format(site)
                main_page = "RCSBLeadAnnotator.html"
            else:
                group_name = "{} - Annotator".format(site)
                main_page = "Annotators.html"

            data = {'group_name' : group_name, 'site' : site, 'main_page' : main_page}
            ret = status = self.runUpdate(table='da_group', where={'code' : code, 'da_group_id' : str(maxgroup)}, data=data)
            if ret != 'OK':
                status = ret

        r = self.getSiteGroupWithCode(site, 'LANN')
        lann_gr = r['group_id']

        data = {'user_name' : site.upper(), 'password': site.upper(), 'email': email, 'initials': site.upper(), 'first_name': first,
                'last_name': last + "(Lead)"}
        ret = status = self.runUpdate(table='da_users', where={'da_group_id' : str(lann_gr)}, data=data)
        if ret != 'OK':
            status = ret

        return status


if __name__ == '__main__':
    db = StatusDbApi(siteId='WWPDB_DEPLOY_TEST_RU', verbose=True, log=sys.stderr)
    message, tentryList = db.getEntryIdListFromInputIdString("G_1002014, G_10020,D_8000210666,1abc,D_8000210646,D_1000210646")
    print(message)
    print(tentryList)
    # """
    # alList = db.getDistinctAnnotatorInitials()
    # print(alList)
    # aaiList = db.getActiveAnnotatorInitials()
    # print aaiList
    # rtList = db.getRetiredAnnotatorInitials()
    # print rtList
    # depids = [ 'D_8000210373', 'D_8000210372' ]
    # rows = db.getGroupIds([ 'D_8000210373', 'D_8000210372' ])
    # print rows
    # ok = db.isTableValid(table=sys.argv[1])
    # if ok:
    #     print 'Table ' + sys.argv[1] + ' exist.'
    # else:
    #     print 'Table ' + sys.argv[1] + ' does not exist.'
    # dir = db.Autenticate(username='JY', password='JY')
    # print dir
    # dir = db.getUserByName(username='JY')
    # print dir
    # dir = db.getUserByEmail(email='jasmin@rcsb.rutgers.edu')
    # print dir
    # ss = str(dir)
    # print 'ss='+ss
    # list = db.getServerInfo()
    # print list
    # """
