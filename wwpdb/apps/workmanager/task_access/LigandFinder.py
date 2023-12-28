##
# File:  LigandFinder.py
# Date:  29-Mar-2020
# Updates:
##
"""

This software was developed as part of the World Wide Protein Data Bank
Common Deposition and Annotation System Project

Copyright (c) 2020 wwPDB

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

from wwpdb.apps.workmanager.db_access.ContentDbApi import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass


class LigandFinder(BaseClass):
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(LigandFinder, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        #
        self.__statusDB = StatusDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        self.__contentDB = ContentDbApi(siteId=self._siteId, verbose=self._verbose, log=self._lfh)
        #
        self.__entryList = self.__statusDB.getEntryListForGroup(groupids=[self._reqObj.getValue("identifier")])

    def getLigandInfo(self):
        """
        """
        if not self.__entryList:
            return {}, "No entry found."
        #
        entryIdList = []
        for entry in self.__entryList:
            if ("dep_set_id" in entry) and entry["dep_set_id"]:
                entryIdList.append(entry["dep_set_id"])
            #
        #
        if not entryIdList:
            return {}, "No entry found."
        #
        ligList = self.__contentDB.getLigandIdList(entryIdList=entryIdList)
        if not ligList:
            return {}, "No ligand found."
        #
        ligMap = {}
        for ligDir in ligList:
            if ("Structure_ID" not in ligDir) or (not ligDir["Structure_ID"]) or ("comp_id" not in ligDir) or \
               (not ligDir["comp_id"]) or (ligDir["comp_id"].upper() == "HOH"):
                continue
            #
            if ligDir["Structure_ID"] in ligMap:
                ligMap[ligDir["Structure_ID"]].append(ligDir["comp_id"].upper())
            else:
                ligMap[ligDir["Structure_ID"]] = [ligDir["comp_id"].upper()]
            #
        #
        if not ligMap:
            return {}, "No ligand found."
        #
        return ligMap, "OK"


if __name__ == '__main__':
    from wwpdb.utils.session.WebRequest import InputRequest
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    siteId = os.getenv("WWPDB_SITE_ID")
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("identifier", "G_1002010")
    myReqObj.setValue("sessionid", "79ae0371518fe08d9d3e1fb8fdd001055632d48a")
    ligFinder = LigandFinder(reqObj=myReqObj, verbose=False, log=sys.stderr)
    retMap, errMsg = ligFinder.getLigandInfo()
    print(errMsg)
    print(retMap)
