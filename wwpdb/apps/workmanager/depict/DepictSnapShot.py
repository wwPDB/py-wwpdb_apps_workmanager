##
# File:  DepictSnapShot.py
# Date:  25-Mar-2016
#
# Updates:
#  09-Dec-2024  zf   call contentDB.getPdbExtIdMap() method to get 'ext_pdb_id'
#
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


import os
import sys

from wwpdb.apps.workmanager.db_access.ContentDbApi import ContentDbApi
from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.depict.DepictBase import processPublicIDs
from wwpdb.apps.workmanager.depict.ReadConFigFile import ReadConFigFile
from wwpdb.apps.workmanager.file_access.SnapShotDiff import SnapShotDiff


class DepictSnapShot(object):
    """
    """
    def __init__(self, reqObj=None, verbose=False, log=sys.stderr):
        """
        """
        self.__reqObj = reqObj
        self.__verbose = verbose
        self.__lfh = log
        self.__depositionid = str(self.__reqObj.getValue("identifier"))
        #
        self.__snapshot_tmplt = ''
        self.__snapshot_diff_tmplt = ''
        self.__snapshot_row_tmplt = ''
        self.__pageContext = ''
        self.__generatePageContent()

    def getPageText(self):
        """
        """
        return self.__pageContext

    def __generatePageContent(self):
        """
        """
        readUtil = ReadConFigFile(reqObj=self.__reqObj, configFile='allfile_config.cif', verbose=self.__verbose, log=self.__lfh)
        configDict = readUtil.read()
        if 'page_template' in configDict:
            if 'snapshot_tmplt' in configDict['page_template']:
                self.__snapshot_tmplt = configDict['page_template']['snapshot_tmplt']['page']
            #
            if 'snapshot_diff_tmplt' in configDict['page_template']:
                self.__snapshot_diff_tmplt = configDict['page_template']['snapshot_diff_tmplt']['page']
            #
            if 'snapshot_row_tmplt' in configDict['page_template']:
                self.__snapshot_row_tmplt = configDict['page_template']['snapshot_row_tmplt']['page']
            #
        #
        if not self.__snapshot_tmplt:
            return
        #
        myD = {}
        statusDB = StatusDbApi(siteId=self.__reqObj.getValue("WWPDB_SITE_ID"), verbose=self.__verbose, log=self.__lfh)
        if statusDB:
            myD = statusDB.getDepInfo(depositionid=self.__depositionid)
        #
        pdbExtIdMap = {}
        contentDB = ContentDbApi(siteId=self.__reqObj.getValue("WWPDB_SITE_ID"), verbose=self.__verbose, log=self.__lfh)
        if contentDB:
            pdbIdList = []
            if ('pdb_id' in myD) and myD['pdb_id']:
                pdbIdList.append(myD['pdb_id'])
            #
            pdbExtIdMap = contentDB.getPdbExtIdMap(pdbIdList)
        #
        myD = processPublicIDs(myD, pdbExtIdMap)
        #
        myD['identifier'] = self.__depositionid
        #
        myD['diffs'] = ''
        ssd = SnapShotDiff(siteId=str(self.__reqObj.getValue("WWPDB_SITE_ID")), verbose=self.__verbose, log=self.__lfh)
        snap = ssd.getSnap(self.__depositionid)
        if not snap:
            myD['type'] = 'Snap not found reset, ' + self.__depositionid + ', last'
            myD['date'] = ''
            myD['time'] = ''
        else:
            try:
                words = snap.split('_')
                myD['type'] = words[0]
                myD['date'] = words[1]
                myD['time'] = words[2]
                diffs = ssd.getDifference(self.__depositionid, snap)
                if diffs:
                    myD['diffs'] = str(self.__depictDifference(diffs))
                #
            except:  # noqa: E722 pylint: disable=bare-except
                myD['type'] = snap
                myD['date'] = ''
                myD['time'] = ''
            #
        #
        self.__pageContext = self.__snapshot_tmplt % myD

    def __depictDifference(self, diff_list):
        """
        """
        if not self.__snapshot_diff_tmplt:
            return ''
        #
        text = ''
        for dif in diff_list:
            myD = {}
            myD['category'] = dif['category']
            myD['rows'] = self.__depictRows(dif['data'])
            text += self.__snapshot_diff_tmplt % myD
        #
        return text

    def __depictRows(self, data_list):
        """
        """
        if not self.__snapshot_row_tmplt:
            return ''
        #
        text = ''
        for data in data_list:
            text += self.__snapshot_row_tmplt % data
        #
        return text


if __name__ == '__main__':
    from wwpdb.utils.config.ConfigInfo import ConfigInfo
    from wwpdb.utils.session.WebRequest import InputRequest
    siteId = 'WWPDB_DEPLOY_TEST_RU'
    # siteId = 'WWPDB_DEPLOY_PRODUCTION_RU'
    os.environ["WWPDB_SITE_ID"] = siteId
    cI = ConfigInfo(siteId)
    #
    myReqObj = InputRequest({}, verbose=True, log=sys.stderr)
    myReqObj.setValue("TopSessionPath", cI.get('SITE_WEB_APPS_TOP_SESSIONS_PATH'))
    myReqObj.setValue("TemplatePath", os.path.join(cI.get('SITE_WEB_APPS_TOP_PATH'), "htdocs", "wfm", "templates"))
    myReqObj.setValue("TopPath", cI.get('SITE_WEB_APPS_TOP_PATH'))
    myReqObj.setValue("WWPDB_SITE_ID", siteId)
    myReqObj.setValue("sessionid", "4f834792f0c20756c57eb8632b4e5d1c5a022f5e")
    myReqObj.setValue("identifier", sys.argv[1])
    snapshot = DepictSnapShot(reqObj=myReqObj, verbose=True, log=sys.stderr)
    print(snapshot.getPageText())
