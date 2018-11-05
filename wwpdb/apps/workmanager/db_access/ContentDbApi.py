##
# File:  ContentDbApi.py
# Date:  15-May-2015
# Updates:
##
"""
Providing addintaional APIs for WFE to get info from db_internal database.

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2015 wwPDB

This software is provided under a Creative Commons Attribution 3.0 Unported
License described at http://creativecommons.org/licenses/by/3.0/.

"""
__docformat__ = "restructuredtext en"
__author__    = "Zukang Feng"
__email__     = "zfeng@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"


import os,sys
from types import *

from wwpdb.api.facade.ConfigInfo                import ConfigInfo
from wwpdb.apps.workmanager.db_access.DbApiUtil import DbApiUtil


class ContentDbApi(object):
    __schemaMap = { "AUDIT_HISTORY" : "select Structure_ID, ordinal, major_revision, minor_revision, revision_date, internal_version from pdbx_audit_revision_history " +
                                      "where Structure_ID = '%s' order by ordinal",
                    "CONTACT_AUTHOR" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID = '%s'",
                    "CONTACT_AUTHOR_LIST" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID in ( '%s' )",
                    "CONTACT_AUTHOR_PI" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID = '%s' " +
                                          "and role = 'principal investigator/group leader'",
                    "CONTACT_AUTHOR_PI_LIST" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID in ( '%s' ) " +
                                               "and role = 'principal investigator/group leader'",
                    "GET_REMINDER_LIST" : "select structure_id from rcsb_status where status_code in ('WAIT','PROC','REPL','AUTH','AUCO') and " +
                                          "rcsb_annotator = '%s' and initial_deposition_date <= DATE_SUB(curdate(), interval 14 day) order by structure_id",
                    "GET_DAILY_STATS" : "select rcsb_annotator from rcsb_status where status_code not in ('PROC','WAIT','POLC','AUCO') " +
                                        "and date_begin_processing  = '%s'",
                    "GET_RANGE_STATS" : "select rcsb_annotator from rcsb_status where status_code not in ('PROC','WAIT','POLC','AUCO') " +
                                        "and date_begin_processing  >= '%s' and date_begin_processing <= '%s'",
                "GET_INPROCESS_STATS" : "select rcsb_annotator, status_code from rcsb_status where status_code in ('WAIT','PROC','AUTH','POLC','REPL')",
                   "GET_RELEASE_DATE" : "select structure_id, pdb_id, date_of_RCSB_release from rcsb_status where structure_id in ( '%s' ) order by structure_id",
                "GET_EM_RELEASE_DATE" : "select structure_id, current_status, map_release_date date_of_EM_release from em_admin where structure_id in ( '%s' ) order by structure_id"
                  }
    """
    """
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        """
        """
        self.__lfh       = log
        self.__verbose   = verbose
        self.__siteId    = siteId
        self.__cI        = ConfigInfo(self.__siteId)
        self.__dbServer  = self.__cI.get("SITE_DB_SERVER")
        self.__dbHost    = self.__cI.get("SITE_DB_HOST_NAME")
        self.__dbName    = "da_internal"
        self.__dbUser    = self.__cI.get("SITE_DB_USER_NAME")
        self.__dbPw      = self.__cI.get("SITE_DB_PASSWORD")
        self.__dbSocket  = self.__cI.get("SITE_DB_SOCKET")
        self.__dbPort    = int(self.__cI.get("SITE_DB_PORT_NUMBER"))
        #
        self.__dbApi = DbApiUtil(dbServer=self.__dbServer, dbHost=self.__dbHost, dbName=self.__dbName, dbUser=self.__dbUser, dbPw=self.__dbPw, \
                                 dbSocket=self.__dbSocket, dbPort=self.__dbPort, verbose=self.__verbose, log=self.__lfh)
        self.__dbApi.setSchemaMap(self.__schemaMap)

    def __getDataDir(self, key, parameter):
        list = self.__dbApi.selectData(key=key, parameter=parameter)
        if list:
            return list[0]
        #
        return None

    def AuditHistory(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__dbApi.selectData(key="AUDIT_HISTORY", parameter=(depositionid))

    def ContactAuthor(self, depositionid=None):
        if not depositionid:
            return None
        #
        if type(depositionid) is ListType:
            return self.__dbApi.selectData(key="CONTACT_AUTHOR_LIST", parameter=("', '".join(depositionid)))
        #
        return self.__dbApi.selectData(key="CONTACT_AUTHOR", parameter=(depositionid))

    def ContactAuthorPI(self, depositionid=None):
        if not depositionid:
            return None
        #
        if type(depositionid) is ListType:
            return self.__dbApi.selectData(key="CONTACT_AUTHOR_PI_LIST", parameter=("', '".join(depositionid)))
        #
        return self.__dbApi.selectData(key="CONTACT_AUTHOR_PI", parameter=(depositionid))

    def getReminderList(self, initial=None):
        if not initial:
            return None
        #
        list = self.__dbApi.selectData(key="GET_REMINDER_LIST", parameter=(initial))
        if not list:
            return None
        #
        id_list = []
        for dir in list:
            id_list.append(dir['structure_id'])
        #
        return id_list

    def getDailyStatsList(self, date=None):
        initial_list = []
        if not date:
            return initial_list
        #
        list = self.__dbApi.selectData(key="GET_DAILY_STATS", parameter=(date))
        return self.__getAnnoList(list)

    def getRangeStatsList(self, startdate=None, enddate=None):
        initial_list = []
        if not startdate or not enddate:
            return initial_list
        #
        list = self.__dbApi.selectData(key="GET_RANGE_STATS", parameter=(startdate, enddate))
        return self.__getAnnoList(list)

    def getInProcessStatsList(self):
        return self.__dbApi.selectData(key="GET_INPROCESS_STATS", parameter=())

    def getReleaseDate(self, id_string):
        emReleaseDateMap = {}
        em_rows = self.__dbApi.selectData(key='GET_EM_RELEASE_DATE', parameter=(id_string))
        if em_rows:
            for row in em_rows:
                if (not 'structure_id' in row) or (not row['structure_id']) or (not 'date_of_EM_release' in row) or \
                   (not row['date_of_EM_release']):
                    continue
                #
                emReleaseDateMap[row['structure_id']] = str(row['date_of_EM_release']).replace(' 00:00:00', '')
            #
        #
        releaseDateMap = {}
        rows = self.__dbApi.selectData(key='GET_RELEASE_DATE', parameter=(id_string))
        if rows:
            for row in rows:
                if (not 'structure_id' in row) or (not row['structure_id']):
                    continue
                #
                if ('pdb_id' in row) and row['pdb_id']:
                    if ('date_of_RCSB_release' in row) and row['date_of_RCSB_release']:
                        releaseDateMap[row['structure_id']] = str(row['date_of_RCSB_release'])
                    #
                elif row['structure_id'] in emReleaseDateMap:
                    releaseDateMap[row['structure_id']] = emReleaseDateMap[row['structure_id']]
                #
            #
        #
        return releaseDateMap

    def runSelectSQL(self, sql):
        return self.__dbApi.runSelectSQL(sql)

    def runUpdate(self, table=None, where=None, data=None):
        return self.__dbApi.runUpdate(table=table, where=where, data=data)

    def __getAnnoList(self, list):
        initial_list = []
        if list:
            for dir in list:
                initial_list.append(dir['rcsb_annotator'])
            #
        #
        return initial_list
