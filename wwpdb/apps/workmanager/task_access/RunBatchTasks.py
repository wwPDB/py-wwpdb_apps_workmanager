#
import argparse
import os
import sys
import textwrap

from wwpdb.apps.workmanager.db_access.StatusDbApi import StatusDbApi
from wwpdb.apps.workmanager.task_access.CifChecker import CifChecker
from wwpdb.apps.workmanager.task_access.PdbFileGenerator import PdbFileGenerator
from wwpdb.apps.workmanager.task_access.RunAnnotationTask import RunAnnotationTask
from wwpdb.apps.workmanager.task_access.RunLigandTask import RunLigandTask
from wwpdb.apps.workmanager.task_access.RunValidationTask import RunValidationTask
from wwpdb.utils.config.ConfigInfo import ConfigInfo
from wwpdb.utils.session.WebRequest import InputRequest

scriptDescription = \
    """This script is for running batch data processes in command line. It requires the proper OneDep system environmental setting
before the script can be run:

For csh/tcsh shell, run the following command:

    source /wwpdb_da/site-config/init/env.csh -h `hostname`

For bash shell, run the following command:

    . /wwpdb_da/site-config/init/env.sh -h `hostname`

The script requires two input arguments to run: one is "task_type", another is "group_id" or "dep_id_list_file".

For example, the following command lines run standard annotation tasks for group 'G_1002010':

   python RunBatchTasks.py --task_type annotation --group_id G_1002010

or

   python RunBatchTasks.py --task_type annotation --dep_id_list_file DepIdListFile

where the DepIdListFile contains the following DepIds:

D_8000000115
D_8000000116

"""
#
task_type_help = \
    """The supported task types are listed in left column.
The corresponding tasks are listed in right column.

annotation : run standard annotation tasks
cifcheck   : run cif dictionary checking
ligand     : run ligand search and update files for autopass cases
mischeck   : run miscellaneous checking
pdbfile    : generate PDB format files
validation : run validation task

"""
#
group_id_help = \
    """The group deposition identifier.

"""
#
dep_id_list_file_help = \
    """The file contains deposition identifier list:

D_xxxxxxxxxx
D_xxxxxxxxxx
......

"""


class RunBatchTasks(object):
    """ Wrapper class responsible for running batch processes
    """
    def __init__(self, verbose=False, log=sys.stderr):
        """
        """
        self.__verbose = verbose
        self.__lfh = log
        #
        self.__siteId = os.getenv("WWPDB_SITE_ID")
        self.__cI = ConfigInfo(self.__siteId)
        #
        self.__reqObj = InputRequest({}, verbose=self.__verbose, log=self.__lfh)
        self.__reqObj.setValue("TopSessionPath", self.__cI.get("SITE_WEB_APPS_TOP_SESSIONS_PATH"))
        self.__reqObj.setValue("WWPDB_SITE_ID", self.__siteId)

    def runWithGroupId(self, task_type=None, group_id=None):
        """
        """
        statusDB = StatusDbApi(siteId=self.__siteId, verbose=self.__verbose, log=self.__lfh)
        retList = statusDB.getEntryListForGroup(groupids=[group_id])
        #
        entryList = []
        for retD in retList:
            if ("dep_set_id" in retD) and retD["dep_set_id"]:
                entryList.append(retD["dep_set_id"])
            #
        #
        if len(entryList) == 0:
            self.__lfh.write("No deposition IDs found for group '%s'.\n" % group_id)
            return
        #
        print(entryList)
        self.__run(task_type=task_type, entryList=entryList)

    def runWithDepIdList(self, task_type=None, file_name=None):
        """
        """
        if not os.access(file_name, os.F_OK):
            self.__lfh.write("File '%s' does not exist.\n" % file_name)
            return
        #
        fin = open(file_name, "r")
        data = fin.read()
        fin.close()
        #
        entryList = []
        for line in data.split("\n"):
            line = line.strip()
            if not line:
                continue
            #
            entryList.append(line)
        #
        if len(entryList) == 0:
            self.__lfh.write("No deposition IDs found in '%s' file.\n" % file_name)
            return
        #
        print(entryList)
        self.__run(task_type=task_type, entryList=entryList)

    def __run(self, task_type=None, entryList=None):
        """
        """
        if entryList is None:
            entryList = []
        if task_type == "annotation":
            obj = RunAnnotationTask(reqObj=self.__reqObj, entryList=entryList, verbose=self.__verbose, log=self.__lfh)
        elif task_type in ("cifcheck", "mischeck"):
            self.__reqObj.setValue("option", task_type)
            obj = CifChecker(reqObj=self.__reqObj, entryList=entryList, verbose=self.__verbose, log=self.__lfh)
        elif task_type == "ligand":
            obj = RunLigandTask(reqObj=self.__reqObj, entryList=entryList, verbose=self.__verbose, log=self.__lfh)
        elif task_type == "pdbfile":
            obj = PdbFileGenerator(reqObj=self.__reqObj, entryList=entryList, verbose=self.__verbose, log=self.__lfh)
        elif task_type == "validation":
            obj = RunValidationTask(reqObj=self.__reqObj, entryList=entryList, verbose=self.__verbose, log=self.__lfh)
        else:
            raise ValueError("unknown task " + task_type)
        #
        message = obj.run()
        self.__lfh.write("%s\n" % message)


if __name__ == "__main__":
    #
    parser = argparse.ArgumentParser(description=scriptDescription, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--task_type", help=textwrap.dedent(task_type_help))
    parser.add_argument("--group_id", help=textwrap.dedent(group_id_help))
    parser.add_argument("--dep_id_list_file", help=textwrap.dedent(dep_id_list_file_help))
    #
    args = parser.parse_args()
    if (args.task_type is None) or ((args.group_id is None) and (args.dep_id_list_file is None)):
        parser.print_help()
        sys.exit(1)
    #
    if args.task_type not in ("annotation", "cifcheck", "ligand", "mischeck", "pdbfile", "validation"):
        print(f'The FILE_TYPE value "{args.task_type}" is not allowed. See below for the allowed FILE_TYPE values.\n')
        parser.print_help()
    #
    taskObj = RunBatchTasks(verbose=True)
    if args.group_id is not None:
        taskObj.runWithGroupId(task_type=args.task_type, group_id=args.group_id)
    elif args.dep_id_list_file is not None:
        taskObj.runWithDepIdList(task_type=args.task_type, file_name=os.path.abspath(args.dep_id_list_file))
    #
