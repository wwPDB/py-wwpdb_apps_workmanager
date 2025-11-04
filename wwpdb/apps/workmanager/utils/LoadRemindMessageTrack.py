##
# File:  LoadRemindMessageTrack.py
# Date:  27-April-2016
# Updates: 31-October-2025 - Refactored to use msgmodule DataAccessLayer instead of CIF file parsing
##
"""
API for loading message receiving/sending information into status database.

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
__version__ = "V0.07"  # TODO: Update version after refactor  # pylint: disable=fixme

import datetime
import getopt
import os
import sys
import time
import traceback

import MySQLdb
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.wf.dbapi.DbConnection import DbConnection

# Import msgmodule utilities - ExtractMessage does the heavy lifting
from wwpdb.apps.msgmodule.util.ExtractMessage import ExtractMessage


class DbApiUtil(object):
    """ Class for making status database connection
    """

    def __init__(self, siteId=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """ Initialization
        """
        self.__siteId = siteId
        # self.__verbose = verbose
        self.__lfh = log
        self.__cI = ConfigInfo(self.__siteId)
        self.__myDb = DbConnection(dbServer=self.__cI.get("SITE_DB_SERVER"),
                                   dbHost=self.__cI.get("SITE_DB_HOST_NAME"),
                                   dbName=self.__cI.get("SITE_DB_DATABASE_NAME"),
                                   dbUser=self.__cI.get("SITE_DB_USER_NAME"),
                                   dbPw=self.__cI.get("SITE_DB_PASSWORD"),
                                   dbPort=int(self.__cI.get("SITE_DB_PORT_NUMBER")),
                                   dbSocket=self.__cI.get("SITE_DB_SOCKET"))
        self.__dbcon = self.__myDb.connect()
        self.__Nretry = 5
        self.__dbState = 0

    def runUpdate(self, table=None, where=None, data=None):
        """ Insertion/Update table based on table name, where condition(s) and data content(s)
        """
        if not table:
            return None
        #
        if (not where) and (not data):
            return None
        #
        rowExists = False
        if where:
            sql = "select * from " + str(table) + " where " + ' and '.join(
                ["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.items()])
            rows = self.runSelectSQL(sql)
            if rows and len(rows) > 0:
                rowExists = True
            #
        #
        if rowExists and (not data):
            return 'OK'
        #
        if rowExists:
            sql = "update " + str(table) + " set " + ','.join(
                ["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in data.items()])
            if "major_issue" not in data:
                sql += ',major_issue = NULL'
            #
            if where:
                sql += ' where ' + ' and '.join(["%s = '%s'" % (k, v.replace("'", "\\'")) for k, v in where.items()])
            #
        else:
            sql = "insert into " + str(table) + " (" + ','.join(['%s' % (k) for k, v in where.items()])
            if data:
                sql += "," + ','.join(['%s' % (k) for k, v in data.items()])
            #
            sql += ") values (" + ','.join(["'%s'" % (v.replace("'", "\\'")) for k, v in where.items()])
            if data:
                sql += "," + ','.join(["'%s'" % (v.replace("'", "\\'")) for k, v in data.items()])
            #
            sql += ")"
        #
        return self.runUpdateSQL(sql)

    def runSelectSQL(self, sql):
        """ Select table row(s) based on sql command
        """
        for retry in range(1, self.__Nretry):
            ret = self.__runSelectSQL(sql)
            if ret is None:
                if self.__dbState > 0:
                    time.sleep(retry * 2)
                    if not self.__reConnect():
                        return None
                else:
                    return None
                #
            else:
                return ret
            #
        #
        return None

    def runUpdateSQL(self, sql):
        """ Insertion/Update table based on sql command
        """
        for retry in range(1, self.__Nretry):
            ret = self.__runUpdateSQL(sql)
            if ret is None:
                if self.__dbState > 0:
                    time.sleep(retry * 2)
                    if not self.__reConnect():
                        return None
                else:
                    return None
                #
            else:
                return ret
            #
        #
        return None

    def __runSelectSQL(self, query):
        """ Execute selection query command
        """
        rows = ()
        try:
            self.__dbcon.commit()
            curs = self.__dbcon.cursor(MySQLdb.cursors.DictCursor)
            curs.execute(query)
            rows = curs.fetchall()
        except MySQLdb.Error as e:
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %d: %s\n" % (e.args[0], e.args[1]))

        return rows

    def __runUpdateSQL(self, query):
        """ Execute insertion/update query command
        """
        try:
            curs = self.__dbcon.cursor()
            curs.execute("set autocommit=0")
            _nrows = curs.execute(query)  # noqa: F841
            self.__dbcon.commit()
            curs.execute("set autocommit=1")
            curs.close()
            return 'OK'
        except MySQLdb.Error as e:
            self.__dbcon.rollback()
            self.__dbState = e.args[0]
            self.__lfh.write("Database error %d: %s\n" % (e.args[0], e.args[1]))
        #
        return None

    def __reConnect(self):
        """ Make database re-connection
        """
        try:
            self.__myDb.close(self.__dbcon)
        except MySQLdb.Error:
            self.__lfh.write("+DbApiUtil.reConnect() DB connection lost - cannot close\n")
            self.__lfh.write("+DbApiUtil.reConnect() Re-connecting to the database ..\n")
            self.__lfh.write("+DbApiUtil.reConnect() UTC time = %s\n" % datetime.datetime.utcnow())
        #
        for i in range(1, self.__Nretry):
            try:
                self.__dbcon = self.__myDb.connect()
                self.__dbState = 0
                return True
            except MySQLdb.Error:
                self.__lfh.write("+DbApiUtil.reConnect() Cannot get re-connection : trying again\n")
                time.sleep(2 * i)
            #
        #
        return False


class LoadRemindMessageTrack(object):
    """ Class for loading message receiving/sending information into status database
    """

    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        """ Initialization
        """
        self.__siteId = siteId
        self.__verbose = verbose
        self.__lfh = log
        self.__statusDB = DbApiUtil(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

        # Use ExtractMessage which automatically handles legacy vs modern communication
        self.__extractMessage = ExtractMessage(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)

    def UpdateBasedIDList(self, depIDList):
        """ Update remind_message_track table based depID list ( comma separate )
        """
        for depID in depIDList.split(','):
            depID = depID.strip()
            self.__updateEntry(depID)
        #

    def UpdateBasedInputIDfromFile(self, filename):
        """ Update remind_message_track table based depID list from file (assume each ID per line)
        """
        if (not os.access(filename, os.F_OK)):
            return
        #
        f = open(filename, 'r')
        data = f.read()
        f.close()
        #
        for depID in data.split('\n'):
            depID = depID.strip()
            self.__updateEntry(depID)
        #

    def __updateEntry(self, depID):
        """ Get remind_message_track information and update table
        """
        if not depID:
            return
        #
        trackMap = self.__getRemindMessageTrack(depID)
        if not trackMap:
            return
        #
        self.__statusDB.runUpdate(table='remind_message_track', where={'dep_set_id': depID}, data=trackMap)

    def __getRemindMessageTrack(self, depID):
        """ Get remind_message_track table information for given depID
        """
        return self.__getRemindMessageTrackFromExtractMessage(depID)

    def __getRemindMessageTrackFromExtractMessage(self, depID):
        """ Get remind_message_track table information using ExtractMessage utility """
        # Use ExtractMessage API methods - let it handle the heavy lifting
        trackMap = {}

        try:
            # Get last message received date from depositor
            last_received = self.__extractMessage.getLastReceivedMsgDatetime(depID)
            if last_received:
                trackMap['last_message_received_date'] = last_received.strftime('%Y-%m-%d')

            # Get last message sent to depositor
            last_sent = self.__extractMessage.getLastSentMsgDatetime(depID)
            if last_sent:
                trackMap['last_message_sent_date'] = last_sent.strftime('%Y-%m-%d')

            # Get last manual reminder sent to depositor
            last_reminder = self.__extractMessage.getLastManualReminderDatetime(depID)
            if last_reminder:
                trackMap['last_reminder_sent_date'] = last_reminder.strftime('%Y-%m-%d')

            # Get last validation report info (returns tuple of datetime and major_issue boolean)
            validation_info = self.__extractMessage.getLastValidation(depID)
            if validation_info[0]:  # validation_info is (datetime, major_issue_boolean)
                trackMap['last_validation_sent_date'] = validation_info[0].strftime('%Y-%m-%d')
                if validation_info[1]:  # major_issue_boolean
                    trackMap['major_issue'] = 'Yes'

        except Exception as e:
            if self.__verbose:
                self.__lfh.write("Error getting message track from ExtractMessage for %s: %s\n" % (depID, str(e)))

        return trackMap


def load_main():
    try:
        opts, _args = getopt.getopt(sys.argv[1:], "i:f:")
        idlist = ''
        filename = ''
        for opt, arg in opts:
            if opt in ("-i"):
                idlist = arg
            elif opt in ("-f"):
                filename = arg
            #
        #
        if idlist or filename:
            siteId = str(os.getenv('WWPDB_SITE_ID'))
            api = LoadRemindMessageTrack(siteId=siteId, verbose=False, log=sys.stderr)
            if idlist:
                api.UpdateBasedIDList(idlist)
            #
            if filename:
                api.UpdateBasedInputIDfromFile(filename)
            #
        #
    except:  # noqa: E722 pylint: disable=bare-except
        traceback.print_exc(file=sys.stderr)
    #


if __name__ == '__main__':
    load_main()
