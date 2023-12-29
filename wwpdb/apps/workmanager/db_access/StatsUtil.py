##
# File:  StatsUtil.py
# Date:  17-July-2015
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

import sys
from datetime import date, timedelta

from wwpdb.apps.workmanager.db_access.ContentDbApi import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.workflow_access.OrderedDict import OrderedDict


class StatsUtil(object):
    """
    """
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):
        """
        """
        self.__siteId = siteId
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__statusDB = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        self.__contentDB = ContentDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        #
        self.__week_day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        self.__today = date.today()
        self.__annoList = self.__statusDB.getActiveAnnoList()

    def getWeeklyStatus(self):
        """
        """
        index, TableColumn, TableData = self.__getInitialTableDef()
        total_dir = {}
        #
        one_day = timedelta(1)
        start_date = self.__today - timedelta(6)
        for _i in range(7):
            plist = self.__contentDB.getDailyStatsList(date=start_date)
            TableData, total_dir = self.__getProcessCount(plist, TableData, total_dir, index)
            date_string = self.__week_day[start_date.weekday()] + ' (' + str(start_date)[5:].replace('-', '/') + ')'
            TableColumn.insert(index, str(index), {'label' : date_string, 'data-field': str(index)})
            start_date += one_day
            index += 1
        #
        TableData = self.__processTotalCount(TableData, total_dir, index)
        TableColumn.insert(index, str(index), {'label' : 'Total', 'data-field': str(index)})
        index += 1
        TableData = self.__processAverageCount(TableData, total_dir, index, 5.0)
        TableColumn.insert(index, str(index), {'label' : 'Average', 'data-field': str(index)})
        return TableColumn.values(), TableData.values()

    def getMonthlyStats(self):
        """
        """
        start_date = self.__today
        week_day = start_date.weekday()
        if week_day > 0:
            start_date -= timedelta(week_day)
        #
        dates_list = []
        for i in range(3):
            start = start_date - timedelta(21 - i * 7)
            end = start + timedelta(6)
            dates_list.append([start, end])
        #
        dates_list.append([start_date, self.__today])
        #
        index, TableColumn, TableData = self.__getInitialTableDef()
        total_dir = {}
        #
        for dates in dates_list:
            slist = self.__contentDB.getRangeStatsList(startdate=dates[0], enddate=dates[1])
            TableData, total_dir = self.__getProcessCount(slist, TableData, total_dir, index)
            date_string = self.__week_day[dates[0].weekday()] + '(' + str(dates[0])[5:].replace('-', '/') + ') - ' \
                + self.__week_day[dates[1].weekday()] + '(' + str(dates[1])[5:].replace('-', '/') + ')'
            TableColumn.insert(index, str(index), {'label' : date_string, 'data-field': str(index)})
            index += 1
        #
        TableData = self.__processTotalCount(TableData, total_dir, index)
        TableColumn.insert(index, str(index), {'label' : 'Total', 'data-field': str(index)})
        index += 1
        TableData = self.__processAverageCount(TableData, total_dir, index, 4.0)
        TableColumn.insert(index, str(index), {'label' : 'Average', 'data-field': str(index)})
        return TableColumn.values(), TableData.values()

    def getProcessStats(self):
        """
        """
        return_list = self.__contentDB.getInProcessStatsList()
        return_dir = {}
        for row in return_list:
            if row['status_code'] in return_dir:
                return_dir[row['status_code']].append(row['rcsb_annotator'])
            else:
                return_dir[row['status_code']] = [row['rcsb_annotator']]
            #
        #
        index, TableColumn, TableData = self.__getInitialTableDef()
        total_dir = {}
        #
        for status in ('WAIT', 'PROC', 'AUTH', 'POLC', 'REPL'):
            found_list = []
            if status in return_dir:
                found_list = return_dir[status]
            #
            TableData, total_dir = self.__getProcessCount(found_list, TableData, total_dir, index)
            TableColumn.insert(index, str(index), {'label' : status, 'data-field': str(index)})
            index += 1
        #
        TableData = self.__processTotalCount(TableData, total_dir, index)
        TableColumn.insert(index, str(index), {'label' : 'Total', 'data-field': str(index)})
        return TableColumn.values(), TableData.values()

    def __getInitialTableDef(self):
        """
        """
        index = 0
        TableColumn = OrderedDict()
        TableColumn.insert(index, str(index), {'label' : 'Annotator', 'data-field': str(index)})
        TableData = OrderedDict()
        count = 0
        for anno in self.__annoList:
            TableData.insert(count, anno['initials'], {str(index) : anno['initials']})
            count += 1
        #
        TableData.insert(count, 'total', {str(index) : 'total'})
        index += 1
        return index, TableColumn, TableData

    def __getProcessCount(self, found_list, TableData, total_dir, index):
        """
        """
        dir = {}  # pylint: disable=redefined-builtin
        for anno in self.__annoList:
            dir[anno['initials']] = 0
        #
        total = 0
        if found_list:
            for ai in found_list:
                if ai not in dir:
                    continue
                #
                dir[ai] += 1
                total += 1
            #
        #
        dir['total'] = total
        #
        for k, v in dir.items():
            TableData[k][str(index)] = str(v)
            if k in total_dir:
                total_dir[k] += v
            else:
                total_dir[k] = v
            #
        #
        return TableData, total_dir

    def __processTotalCount(self, TableData, total_dir, index):
        """
        """
        for k, v in total_dir.items():
            TableData[k][str(index)] = str(v)
        #
        return TableData

    def __processAverageCount(self, TableData, total_dir, index, denominator):
        """
        """
        for k, v in total_dir.items():
            TableData[k][str(index)] = '%.2f' % (v / denominator)
        #
        return TableData


if __name__ == '__main__':
    st = StatsUtil(siteId='WWPDB_DEPLOY_TEST_RU', verbose=True, log=sys.stderr)
    column, data = st.getWeeklyStatus()
    print(column)
    print(data)
    column1, data1 = st.getMonthlyStats()
    print(column1)
    print(data1)
    column2, data2 = st.getProcessStats()
    print(column2)
    print(data2)
