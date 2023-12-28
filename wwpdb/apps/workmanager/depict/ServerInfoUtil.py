##
# File:  ServerInfoUtil.py
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
__author__ = "Zukang Feng"
__email__ = "zfeng@rcsb.rutgers.edu"
__license__ = "Creative Commons Attribution 3.0 Unported"
__version__ = "V0.07"


import sys

from wwpdb.utils.wf.dbapi.WFEtime import getTimeNow
from wwpdb.apps.workmanager.depict.DepictBase import DepictBase


class ServerInfoUtil(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(ServerInfoUtil, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #

    def getServerInfo(self):
        """
        """
        text = ''
        timeNow = getTimeNow()
        self._connectStatusDB()
        if self._statusDB:
            serverList = self._statusDB.getServerInfo()
            for server in serverList:
                dataD = {}
                dataD['host'] = server['hostname']
                dif = (round(float(timeNow) - float(server['status_timestamp']))) / 10.0
                dataD['time'] = str(dif)
                if dif < 1.1:
                    dataD['comment'] = 'Good'
                elif dif < 2.1:
                    dataD['comment'] = 'OK'
                elif dif < 5.1:
                    dataD['comment'] = 'Poor'
                else:
                    dataD['comment'] = 'Unavailable'
                #
                self._dataInfo['server_info_tmplt'] = [dataD]
                text += self.getPageText(page_id='server_info_tmplt')
            #
        #
        return text
