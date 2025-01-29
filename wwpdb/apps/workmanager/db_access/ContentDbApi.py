##
# File:  ContentDbApi.py
# Date:  15-May-2015
#
# Updates:
#  09-Dec-2024  zf   add getPdbExtIdMap() method.
#
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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys

from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.apps.workmanager.db_access.DbApiUtil import DbApiUtil


class ContentDbApi(object):
    __schemaMap = { "AUDIT_HISTORY" : "select h.Structure_ID, h.ordinal, h.major_revision, h.minor_revision, h.revision_date, h.internal_version, d.description from pdbx_audit_revision_history as h " +
                         "LEFT JOIN pdbx_audit_revision_details d ON h.Structure_ID = d.Structure_ID and h.ordinal = d.revision_ordinal and d.type='Coordinate replacement' " +
                         "where h.Structure_ID = '%s' order by ordinal",
                    "CONTACT_AUTHOR" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID = '%s'",
                    "CONTACT_AUTHOR_LIST" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID in ( '%s' )",
                    "CONTACT_AUTHOR_PI" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID = '%s' " +
                                          "and role = 'principal investigator/group leader'",
                    "CONTACT_AUTHOR_PI_LIST" : "select Structure_ID as id, email, name_first, name_mi, name_last, role, country from pdbx_contact_author where Structure_ID in ( '%s' ) " +
                                               "and role = 'principal investigator/group leader'",
                    "GET_REMINDER_LIST" : "select structure_id from rcsb_status where status_code in ('WAIT','PROC','REPL','AUTH','AUCO') and " +
                                          "rcsb_annotator = '%s' and initial_deposition_date <= DATE_SUB(curdate(), interval 21 day) order by structure_id",
                    "GET_DAILY_STATS" : "select rcsb_annotator from rcsb_status where status_code not in ('PROC','WAIT','POLC','AUCO') " +
                                        "and date_begin_processing  = '%s'",
                    "GET_RANGE_STATS" : "select rcsb_annotator from rcsb_status where status_code not in ('PROC','WAIT','POLC','AUCO') " +
                                        "and date_begin_processing  >= '%s' and date_begin_processing <= '%s'",
                "GET_INPROCESS_STATS" : "select rcsb_annotator, status_code from rcsb_status where status_code in ('WAIT','PROC','AUTH','POLC','REPL')",
                   "GET_RELEASE_DATE" : "select structure_id, pdb_id, date_of_RCSB_release from rcsb_status where structure_id in ( '%s' ) order by structure_id",
                "GET_EM_RELEASE_DATE" : "select structure_id, current_status, map_release_date date_of_EM_release from em_admin where structure_id in ( '%s' ) order by structure_id",
                 "GET_REPLACE_COUNTS" : "select s2.name, s2.identifier_ORCID, sum(s2.count) as numreplace from " +
                        "(select c.identifier_ORCID, CONCAT('', c.name_last, ', ', c.name_first) as name, s1.count from pdbx_contact_author as c, " + 
                        "(select d.Structure_id, count(d.Structure_id) as count   from pdbx_audit_revision_details as d, pdbx_audit_revision_history as h where " +
                        "h.Structure_id = d.Structure_id and h.ordinal = d.revision_ordinal and d.type='Coordinate replacement' and DATEDIFF(CURDATE(), h.revision_date) <= 365 " +
                        "group by d.Structure_id  ) s1  where s1.Structure_id = c.Structure_Id and c.role='principal investigator/group leader' " +
                        "order by c.identifier_ORCID ) s2 group by identifier_ORCID, name order by name",
                 "GET_LIGAND_ID_LIST" : "select Structure_ID, comp_id from pdbx_entity_nonpoly where Structure_ID in ( '%s' )",
                 "GET_EXT_PDB_ID_INFO": "select distinct database_code,pdbx_database_accession from database_2 where database_id = 'PDB' and pdbx_database_accession " +
                                        "is not NULL and pdbx_database_accession != '' and database_code in ( '%s' )"
                   }
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
        self.__dbName = "da_internal"
        self.__dbUser = self.__cI.get("SITE_DB_USER_NAME")
        self.__dbPw = self.__cI.get("SITE_DB_PASSWORD")
        self.__dbSocket = self.__cI.get("SITE_DB_SOCKET")
        self.__dbPort = int(self.__cI.get("SITE_DB_PORT_NUMBER"))
        #
        self.__dbApi = DbApiUtil(dbServer=self.__dbServer, dbHost=self.__dbHost, dbName=self.__dbName, dbUser=self.__dbUser, dbPw=self.__dbPw,
                                 dbSocket=self.__dbSocket, dbPort=self.__dbPort, verbose=self.__verbose, log=self.__lfh)
        self.__dbApi.setSchemaMap(self.__schemaMap)

    # def __getDataDir(self, key, parameter):
    #     rlist = self.__dbApi.selectData(key=key, parameter=parameter)
    #     if rlist:
    #         return rlist[0]
    #     #
    #     return None

    def AuditHistory(self, depositionid=None):
        if not depositionid:
            return None
        #
        return self.__dbApi.selectData(key="AUDIT_HISTORY", parameter=(depositionid))

    def ContactAuthor(self, depositionid=None):
        if not depositionid:
            return None
        #
        if isinstance(depositionid, list):
            return self.__dbApi.selectData(key="CONTACT_AUTHOR_LIST", parameter=("', '".join(depositionid)))
        #
        return self.__dbApi.selectData(key="CONTACT_AUTHOR", parameter=(depositionid))

    def ContactAuthorPI(self, depositionid=None):
        if not depositionid:
            return None
        #
        if isinstance(depositionid, list):
            return self.__dbApi.selectData(key="CONTACT_AUTHOR_PI_LIST", parameter=("', '".join(depositionid)))
        #
        return self.__dbApi.selectData(key="CONTACT_AUTHOR_PI", parameter=(depositionid))

    def getReminderList(self, initial=None):
        if not initial:
            return None
        #
        tlist = self.__dbApi.selectData(key="GET_REMINDER_LIST", parameter=(initial))
        if not tlist:
            return None
        #
        id_list = []
        for row in tlist:
            id_list.append(row['structure_id'])
        #
        return id_list

    def getDailyStatsList(self, date=None):
        initial_list = []
        if not date:
            return initial_list
        #
        rlist = self.__dbApi.selectData(key="GET_DAILY_STATS", parameter=(date))
        return self.__getAnnoList(rlist)

    def getRangeStatsList(self, startdate=None, enddate=None):
        initial_list = []
        if not startdate or not enddate:
            return initial_list
        #
        rlist = self.__dbApi.selectData(key="GET_RANGE_STATS", parameter=(startdate, enddate))
        return self.__getAnnoList(rlist)

    def getInProcessStatsList(self):
        return self.__dbApi.selectData(key="GET_INPROCESS_STATS", parameter=())

    def getReleaseDate(self, id_string):
        emReleaseDateMap = {}
        em_rows = self.__dbApi.selectData(key='GET_EM_RELEASE_DATE', parameter=(id_string))
        if em_rows:
            for row in em_rows:
                if ('structure_id' not in row) or (not row['structure_id']) or ('date_of_EM_release' not in row) or \
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
                if ('structure_id' not in row) or (not row['structure_id']):
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

    def GetReplaceCounts(self):
        #
        return self.__dbApi.selectData(key="GET_REPLACE_COUNTS")

    def getLigandIdList(self, entryIdList=None):
        #
        if not entryIdList:
            return None
        #
        return self.__dbApi.selectData(key="GET_LIGAND_ID_LIST", parameter=("', '".join(entryIdList)))

    def getPdbExtIdMap(self, pdbIdList):
        pdbExtIdMap = {}
        if len(pdbIdList) > 0:
            rows = self.__dbApi.selectData(key="GET_EXT_PDB_ID_INFO", parameter=("', '".join(pdbIdList)))
            for row in rows:
                if ('database_code' in row) and row['database_code'] and ('pdbx_database_accession' in row) and row['pdbx_database_accession']:
                    pdbExtIdMap[row['database_code']] = row['pdbx_database_accession']
                #
            #
        #
        return pdbExtIdMap

    def runSelectSQL(self, sql):
        return self.__dbApi.runSelectSQL(sql)

    def runUpdate(self, table=None, where=None, data=None):
        return self.__dbApi.runUpdate(table=table, where=where, data=data)

    def __getAnnoList(self, rlist):
        initial_list = []
        if rlist:
            for row in rlist:
                initial_list.append(row['rcsb_annotator'])
            #
        #
        return initial_list
