#-*-coding:utf-8;-*-
from errno import EISDIR,ENOENT
from json import dumps,load
from os.path import abspath,dirname,exists,expandvars,isfile,join
from socket import AF_INET,SOCK_STREAM,SocketType,socket
from subprocess import run
from tempfile import NamedTemporaryFile
from time import time_ns
from typing import Any,Optional
from urllib.parse import quote,urlunsplit
MODULE_PATH=dirname(__spec__.origin)
CONFIG=load(open(join(MODULE_PATH,"config.json"),"r",encoding="utf-8"))
AUTO_RUNNER=open(join(MODULE_PATH,"autorunner.js"),"r",encoding="utf-8").read()
FILE_RUNNER=open(join(MODULE_PATH,"filerunner.js"),"r",encoding="utf-8").read()
STRING_RUNNER=open(join(MODULE_PATH,"stringrunner.js"),"r",encoding="utf-8").read()
def bindAvailablePort(unboundSocket:SocketType,listenBacklog:Optional[int]=None,connectAddress:Any=None)->int:
    port=CONFIG["min_port"]
    while True:
        address=(CONFIG["host_name"],port)
        try:
            unboundSocket.bind(address)
        except OSError:
            if port<CONFIG["max_port"]:
                port+=1
            else:
                raise OverflowError("No available ports found")
        else:
            break
    if connectAddress is None:
        if listenBacklog is not None:
            unboundSocket.listen(int(listenBacklog))
    else:
        unboundSocket.connect(connectAddress)
    return port
def runAutoFile(filePath:str)->None:
    absolutePath=abspath(str(filePath))
    if not exists(absolutePath):
        raise FileNotFoundError(ENOENT,"The file doesn't exist",filePath)
    if not isfile(absolutePath):
        raise IsADirectoryError(EISDIR,"The path belongs to a directory",filePath)
    with socket(AF_INET,SOCK_STREAM) as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(AUTO_RUNNER%(serverPort,))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"-W","--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                clientSocket.sendall((dumps({"file":absolutePath,"path":dirname(absolutePath)},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
def runFile(filePath:str)->None:
    absolutePath=abspath(str(filePath))
    if not exists(absolutePath):
        raise FileNotFoundError(ENOENT,"The file doesn't exist",filePath)
    if not isfile(absolutePath):
        raise IsADirectoryError(EISDIR,"The path belongs to a directory",filePath)
    with socket(AF_INET,SOCK_STREAM) as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(FILE_RUNNER%(serverPort,))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"-W","--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                clientSocket.sendall((dumps({"file":absolutePath,"path":dirname(absolutePath)},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
def runString(commandString:str,commandTitle:Optional[str]=None)->None:
    with socket(AF_INET,SOCK_STREAM) as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(STRING_RUNNER%(serverPort,))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"-W","--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                if commandTitle is None:
                    usedTitle="%s-%d"%(CONFIG["command_title"],time_ns())
                else:
                    usedTitle=str(commandTitle)
                clientSocket.sendall((dumps({"name":usedTitle,"script":str(commandString)},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))