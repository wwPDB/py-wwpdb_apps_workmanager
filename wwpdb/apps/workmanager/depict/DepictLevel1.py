##
# File:  DepictLevel1.py
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

from wwpdb.apps.workmanager.depict.DepictBase import DepictBase
from wwpdb.apps.workmanager.depict.Level1Util import Level1Util
from wwpdb.apps.workmanager.depict.ServerInfoUtil import ServerInfoUtil


class DepictLevel1(DepictBase):
    """
    """
    def __init__(self, reqObj=None, statusDB=None, conFigObj=None, verbose=False, log=sys.stderr):
        """
        """
        super(DepictLevel1, self).__init__(reqObj=reqObj, statusDB=statusDB, conFigObj=conFigObj, verbose=verbose, log=log)
        #
        self.__setup()

    def __setup(self):
        """
        """
        dataD = {}
        dataD['breadcrumbs'] = '[1]Deposition Summary'
        dataD['pageTitle'] = 'Deposition Summary : Level 1 :'
        dataD['comment_start'] = ' '
        dataD['comment_end'] = ' '
        #
        self._connectStatusDB()
        self._getUserInfoDict()
        #
        if self._userInfo and ('code' in self._userInfo) and self._userInfo['code'] == 'DEP':
            dataD['breadcrumbs'] = '[1]Summary of entries being deposited'
            dataD['comment_start'] = '<!--'
            dataD['comment_end'] = '-->'
        #
        if self._userInfo and ('code' in self._userInfo) and self._userInfo['code'] == 'LANN':
            dataD['pageTitle'] = '[Level 1] Lead Annotator Screen'
            dataD['comment_start'] = '<!--'
            dataD['comment_end'] = '-->'
        #
        self._dataInfo['level1_tmplt'] = [dataD]
        level1Util = Level1Util(reqObj=self._reqObj, statusDB=self._statusDB, conFigObj=self._conFigObj, verbose=self._verbose, log=self._lfh)
        self._UtilClass['Level1Util'] = level1Util
        sInfoUtil = ServerInfoUtil(reqObj=self._reqObj, statusDB=self._statusDB, conFigObj=self._conFigObj, verbose=self._verbose, log=self._lfh)
        self._UtilClass['ServerInfoUtil'] = sInfoUtil
