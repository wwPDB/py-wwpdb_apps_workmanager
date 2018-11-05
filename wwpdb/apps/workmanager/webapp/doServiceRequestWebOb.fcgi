#!/opt/wwpdb/bin/python
#
# File:     doServiceRequestWebOb.fcgi
# Created:  11-Mar-2010
#
# Updated:
# 20-Apr-2010 JW    Ported to seqmodule package
# 25-Jul-2010 JW    Ported to ccmodule package
# 21-Sep-2011 RPS   "WWPDB_SITE_ID" now captured via Apache environment parameter
#					and setting of topPath now delegated to WebApp object
# 02-Oct-2012 ZK    Ported to entity_transform package
# 09-Oct-2012 RPS   Now referencing python interpreter at /opt/wwpdb/bin/python.
"""
This top-level responder for requests to /services/.... url for the
wwPDB Chemical Component editor application framework.

This version depends on FCGI and WebOb.

Adapted from mod_wsgi version -

"""
__docformat__ = "restructuredtext en"
__author__    = "John Westbrook"
__email__     = "jwest@rcsb.rutgers.edu"
__license__   = "Creative Commons Attribution 3.0 Unported"
__version__   = "V0.07"

import sys,traceback
from webob import Request, Response
from wwpdb.utils.rcsb.fcgi  import WSGIServer

#  - URL mapping and application specific classes are launched from WorkManagerWebApp()
from wwpdb.apps.workmanager.webapp.WorkManagerWebApp import WorkManagerWebApp


class MyRequestApp(object):
    """  Handle server interaction using FCGI/WSGI and WebOb Request
         and Response objects.
    """
    def __init__(self,textString="Initialized from contructor",verbose=False,log=sys.stderr):
        """ 
        """
        self.__text=textString
        self.__verbose=verbose
        self.__lfh=log
        self.__siteId=None
        self._myParameterDict={}        
        
    def __dumpEnv(self,request):
        outL=[]
        #outL.append('<pre align="left">')
        outL.append("\n------------------doServiceRequest()------------------------------\n")
        outL.append("Web server request data content:\n")                
        outL.append("Text initialization:   %s\n" % self.__text)        
        try:
            outL.append("Host:         %s\n" % request.host)
            outL.append("Path:         %s\n" % request.path)
            outL.append("Method:       %s\n" % request.method)        
            outL.append("Query string: %s\n" % request.query_string)
            outL.append("Parameter List:\n")
            for name,value in request.params.items():
                outL.append("Request parameter:    %s:  %r\n" % (name,value))
        except:
            traceback.print_exc(file=self.__lfh)            

        outL.append("\n------------------------------------------------\n\n")
        #outL.append("</pre>")
        return outL

    def __call__(self, environment, responseApplication):
        """          WSGI callable entry point


        """
        myRequest  = Request(environment)
        #
        self._myParameterDict={}   
        try:
            if environment.has_key('WWPDB_SITE_ID'):
                self.__siteId=environment['WWPDB_SITE_ID']
                self.__lfh.write("+MyRequestApp.__call__() - WWPDB_SITE_ID environ variable captured as %s\n" % self.__siteId)
            for name,value in environment.items():
                self.__lfh.write("+MyRequestApp.__call__() - ENVIRON parameter:    %s:  %r\n" % (name,value))
            for name,value in myRequest.params.items():
                if (not self._myParameterDict.has_key(name)):
                    self._myParameterDict[name]=[]
                self._myParameterDict[name].append(value)
            self._myParameterDict['request_path']=[myRequest.path.lower()]
        except:
            traceback.print_exc(file=self.__lfh)            
            self.__lfh.write("+MyRequestApp.__call__() - contents of request data\n")
            self.__lfh.write("%s" % ("".join(self.__dumpEnv(request=myRequest))))
            
        ###
        ### At this point we have everything needed from the request !
        ###
        myResponse = Response()
        myResponse.status       = '200 OK'
        myResponse.content_type = 'text/html'       
        ###
        ###  Application specific functionality called here --
        ###  Application receives path and parameter info only!
        ###
        relmodule = WorkManagerWebApp(parameterDict=self._myParameterDict,verbose=self.__verbose, 
                           log=self.__lfh,siteId=self.__siteId)
        rspD = relmodule.doOp()
        myResponse.content_type = rspD['CONTENT_TYPE']
        myResponse.body = rspD['RETURN_STRING']
        if rspD.has_key('ENCODING'):
            myResponse.content_encoding = rspD['ENCODING']
        if rspD.has_key('DISPOSITION'):
            myResponse.content_disposition = rspD['DISPOSITION']
        ####
        ###
        return myResponse(environment,responseApplication)
##
##  NOTE -  Path to top of the web application tree and verbose setting are set here ONLY! 
##
WSGIServer(MyRequestApp(textString="doServiceRequest() - WebOb version",verbose=True,log=sys.stderr)).run()
#













