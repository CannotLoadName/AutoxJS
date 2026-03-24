#-*-coding:utf-8;-*-
from . import get_autox_js_client_script
from autoxjs import runString,forceStop
def startServer()->None:
    runString(get_autox_js_client_script(),"autox-client")
def stopServer()->None:
    forceStop(("autox-client",),True)