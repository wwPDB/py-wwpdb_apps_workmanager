##
# File:  CifChecker.py
# Date:  26-Apr-2017
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

import os
import sys

from mmcif.io.IoAdapterCore import IoAdapterCore as IoAdapter
from wwpdb.apps.workmanager.task_access.BaseClass import BaseClass


class CifChecker(BaseClass):
    def __init__(self, reqObj=None, entryList=None, verbose=False, log=sys.stderr):
        """
        """
        super(CifChecker, self).__init__(reqObj=reqObj, verbose=verbose, log=log)
        self.__entryList = entryList
        self.__dictRoot = os.path.abspath(self._cICommon.get_mmcif_dict_path())
        self.__dictName = self._cICommon.get_mmcif_archive_current_dict_filename() + ".sdb"
        self.__option = self._reqObj.getValue("option")
        #
        self.__optionDict = {"cifcheck" : ["CIF DICTIONARY", "_CifChecker", "_CifChecker.cif", "_CifChecker.cif-diag.log",
                                           "_CifChecker.log", "_CifChecker_cmd.log"],
                             "mischeck" : ["MISCELLANEOUS", "_MisChecker", "_MisChecker.cif", "_MiscChecking.txt",
                                           "_MisChecker.log", "_MisChecker_cmd.log"]}
        #

    def run(self):
        """
        """
        if (self.__option != "cifcheck") and (self.__option != "mischeck"):
            return "No task was defined!"
        #
        self._setupGroupTaskPickle()
        self._runMultiProcess(classMethod="runMulti", inputDataList=self.__entryList)
        return self.__getReturnMessage()

    def runMulti(self, dataList, procName, optionsD, workingDir):  # pylint: disable=unused-argument
        """
        """
        rList = []
        for entry_id in dataList:
            self.__runSingle(entry_id)
            rList.append(entry_id)
        #
        return rList, rList, []

    def __runSingle(self, entry_id):
        modelFile = self._getExistingArchiveFileWithPickleMessage(entry_id, "model", "pdbx", "latest", self.__optionDict[self.__option][1])
        if modelFile:
            self.__checkModelFile(entry_id, modelFile)
        #

    def __checkModelFile(self, entry_id, inputFile):
        localModelFile = entry_id + self.__optionDict[self.__option][2]
        outputFile = entry_id + self.__optionDict[self.__option][3]
        logFile = entry_id + self.__optionDict[self.__option][4]
        clogFile = entry_id + self.__optionDict[self.__option][5]
        for fileName in (localModelFile, outputFile, logFile, clogFile):
            self._removeFile(os.path.join(self._sessionPath, fileName))
        #
        if self.__option == "cifcheck":
            message = self._copyFileUtil(inputFile, os.path.join(self._sessionPath, localModelFile))
            if message:
                self._dumpPickle(entry_id + self.__optionDict[self.__option][1], message)
                return
            #
            options = " -dictSdb " + os.path.join(self.__dictRoot, self.__dictName) + " -f " + localModelFile
            cmd = self._getCmd("${DICTBINPATH}/CifCheck", "", "", "", clogFile, options)
        else:
            cmd = self._getCmd("${BINPATH}/MiscChecking", inputFile, outputFile, logFile, clogFile, "")
        #
        self._runCmd(cmd)
        #
        for fileName in (localModelFile, logFile, clogFile):
            self._removeFile(os.path.join(self._sessionPath, fileName))
        #
        if self.__option == "mischeck":
            self.__runGeometricChecking(entry_id, inputFile)
        #
        self._dumpPickle(entry_id + self.__optionDict[self.__option][1], "OK")

    def __getReturnMessage(self):
        message = ""
        for entry_id in self.__entryList:
            pickleData = self._loadPickle(entry_id + self.__optionDict[self.__option][1])
            error = ""
            if pickleData and pickleData != "OK":
                error = pickleData + "\n"
            #
            logFile = os.path.join(self._sessionPath, entry_id + self.__optionDict[self.__option][3])
            if os.access(logFile, os.F_OK):
                f = open(logFile, "r")
                error += f.read() + "\n"
                f.close()
            #
            if error:
                message += self.__optionDict[self.__option][0] + " CHECK FOR " + entry_id + ":\n" + error
            else:
                message += self.__optionDict[self.__option][0] + " CHECK FOR " + entry_id + ": OK.\n"
            #
            self._removePickle(entry_id + self.__optionDict[self.__option][1])
        #
        self._updateGroupTaskPickle(message)
        #
        return message

    def __runGeometricChecking(self, entry_id, inputFile):
        readIoObj = IoAdapter()
        cifContainerList = readIoObj.readFile(inputFile)
        if len(cifContainerList) == 0:
            return
        #
        chiralMsg = ""
        chiralObj = cifContainerList[0].getObj("pdbx_validate_chiral")
        if chiralObj:
            caveatObj = cifContainerList[0].getObj("database_PDB_caveat")
            if caveatObj:
                for rowIndex in range(caveatObj.getRowCount()):
                    text = self.__getValue(caveatObj, "text", rowIndex)
                    if text == "":
                        continue
                    #
                    if chiralMsg != "":
                        chiralMsg += "\n"
                    #
                    chiralMsg += text
                #
            #
        #
        contactMsg = ""
        for category in ("pdbx_validate_close_contact", "pdbx_validate_symm_contact"):
            contactObj = cifContainerList[0].getObj(category)
            if contactObj:
                text = self.__getCloseContactInfo(contactObj)
                if text == "":
                    continue
                #
                if contactMsg != "":
                    contactMsg += "\n"
                #
                contactMsg += text
            #
        #
        if (chiralMsg == "") and (contactMsg == ""):
            return
        #
        message = ""
        if chiralMsg != "":
            message = "\nChirality errors in your coordinates have been indicated in section 5.1 (Standard geometry) or 5.4 (nonstandard\n"
            message += "residues in protein, DNA, RNA chains) or 5.6 (Ligand geometry) in the PDF validation report. These errors are\n"
            message += "highlighted in the database_PDB_caveat section of the coordinate CIF file.\n\n"
            message += chiralMsg
            message += "\n\nPlease upload new coordinates to resolve this issue."
        #
        if contactMsg != "":
            if message != "":
                message += "\n"
            #
            message += "\nSection 5.2 (Close contacts) of the validation report includes at least one physically unrealistic interatomic\n"
            message += "distance. Please upload a new coordinate file that resolves any issues or send correspondence clarifying the\n"
            message += "situation.\n\n"
            message += "   Chain Atom       Res  Seq     Chain Atom       Res  Seq  Symm_Code   Distance\n"
            message += contactMsg
        #
        logFile = os.path.join(self._sessionPath, entry_id + self.__optionDict[self.__option][3])
        if os.access(logFile, os.F_OK):
            fin = open(logFile, "r")
            error = fin.read()
            fin.close()
            #
            if error != "":
                message += "\n\n" + error
            #
        #
        fout = open(logFile, "w")
        fout.write(message)
        fout.close()

    def __getValue(self, catObj, attribute, rowIdx):
        """ Get a value from attributeName="attribute", rowIndex="rowIdx" in catetory object "catObj".
        """
        value = ""
        try:
            value = catObj.getValue(attributeName=attribute, rowIndex=rowIdx)
            if (value is None) or (value == ".") or (value == "?"):
                value = ""
            #
            value = value.strip()
        except:  # noqa: E722 pylint: disable=bare-except
            value = ""
        #
        return value

    def __getCloseContactInfo(self, catObj):
        text = ""
        for rowIndex in range(catObj.getRowCount()):
            dist = self.__getValue(catObj, "dist", rowIndex)
            if dist == "":
                continue
            #
            try:
                if float(dist) > 1.0:
                    continue
            except:  # noqa: E722 pylint: disable=bare-except
                continue
            #
            if text != "":
                text += "\n"
            #
            text += "   " + self.__get_atom(catObj, "1", rowIndex) + " - " + self.__get_atom(catObj, "2", rowIndex)
            #
            cs = self.__getValue(catObj, "site_symmetry_2", rowIndex)
            if cs == "":
                cs = "1_555"
            #
            text += " " + "%8s" % cs
            #
            text += "   Dist = " + "%.2f" % float(dist)
        #
        return text

    def __get_atom(self, catObj, suffix, rowIndex):
        chain_id = self.__getValue(catObj, "auth_asym_id_" + suffix, rowIndex)
        atom_name = self.__getValue(catObj, "auth_atom_id_" + suffix, rowIndex)
        cs = self.__getValue(catObj, "label_alt_id_" + suffix, rowIndex)
        alt_id = "   "
        if cs != "":
            alt_id = "(" + cs + ")"
        #
        res_name = self.__getValue(catObj, "auth_comp_id_" + suffix, rowIndex)
        res_num = self.__getValue(catObj, "auth_seq_id_" + suffix, rowIndex)
        ins_code = self.__getValue(catObj, "PDB_ins_code_" + suffix, rowIndex)
        if ins_code:
            ins_code = " "
        #
        return "%5s" % chain_id + " %4s" % atom_name + " %3s" % alt_id + " %5s" % res_name + " %4s" % res_num + " %1s" % ins_code
