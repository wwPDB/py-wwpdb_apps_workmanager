##
# File:  SnapShotDiff.py
# Date:  23-June-2015
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


import os
import sys
import pickle

from wwpdb.apps.wf_engine.engine.WFEapplications import getPicklePath


class SnapShotDiff(object):
    """
    """
    def __init__(self, siteId=None, verbose=False, log=sys.stderr):  # pylint: disable=unused-argument
        """
        """
        # self.__siteId = siteId
        # self.__verbose = verbose
        self.__lfh = log

    def getSnap(self, depID):
        """ Method to return the file handle path for a file system snapshot
            name is the type of snapshot like reset or upload
            Only the last snapshot is supported at this time
        """
        path = getPicklePath(depID)
        if not os.access(path, os.F_OK):
            return None
        #
        snap = [temp for temp in os.listdir(path) if os.path.isdir(os.path.join(path, temp)) and temp.startswith('reset')]
        #
        if not snap:
            return None
        #
        snap.sort(key=lambda x: os.stat(os.path.join(path, x)).st_mtime)
        return snap[-1]

    def getDifference(self, depID, snap):
        """ Method to check all categories in a snapshot and return all differences
            Look for all pickle files - and compare each matching file name
        """
        path = getPicklePath(depID)
        #
        ret = []
        dlist = os.listdir(path)
        for filename in dlist:
            if filename[-4:] == '.pkl':
                olddat = self.__getData(os.path.join(path, filename))
                newdat = self.__getData(os.path.join(path, snap, filename))
                if olddat and newdat:
                    diff = self.__difData(filename, olddat, newdat)
                    if diff and ('data' in diff) and diff['data']:
                        ret.append(diff)
                    #
                #
            #
        #
        return ret

    def __getData(self, filename):
        """ Get an object as the contents of a named pickle file
        """
        try:
            f = open(filename, 'rb')
            ret = pickle.load(f)
            f.close()
            return ret
        except Exception as e:
            self.__lfh.write("Exception=%s\n" % str(e))
            return None
        #

    def __difData(self, filename, olddat, newdat):
        """ Method to compare the contents of 2 category pickle files
            Returns a dictionary of differences
        """
        ret = {}
        try:
            dif = []
            if ('items' in olddat) and ('items' in newdat):
                items1 = olddat['items']
                items2 = newdat['items']
                ints1 = len(items1)
                ints2 = len(items2)
                if ints1 == ints2:
                    n = 0
                    for (i1, i2) in zip(items1, items2):
                        n = n + 1
                        for item1, value1 in i1.items():
                            if not (item1.endswith('_ordinal') or item1 == 'id') :
                                if item1 in i2.keys():
                                    value2 = i2[item1]
                                    if value1['value'] != value2['value']:
                                        d = {}
                                        d['instance'] = n
                                        d['item'] = item1
                                        d['d1'] = value1['value']
                                        d['d2'] = value2['value']
                                        dif.append(d)
                                    #
                                else:
                                    d = {}
                                    d['instance'] = n
                                    d['item'] = item1
                                    d['d1'] = "Item missing"
                                    d['d2'] = "Item missing"
                                    dif.append(d)
                                #
                            #
                        #
                    #
                else:
                    d = {}
                    d['instance'] = 0
                    d['item'] = 'Length of category has changed'
                    d['d1'] = str(ints1)
                    d['d2'] = str(ints2)
                    dif.append(d)
                #
            #
            if dif:
                ret['category'] = filename[0:-4]
                ret['data'] = dif
            #
        except Exception as e:
            self.__lfh.write("Exception=%s\n" % str(e))
        #
        return ret


def main_snap():
    ssd = SnapShotDiff(siteId="WWPDB_DEPLOY_INTERNAL")
    snap = ssd.getSnap('D_1100209960')
    print(snap)
    diff = ssd.getDifference('D_1100209960', snap)
    print(diff)


if __name__ == '__main__':
    main_snap()
