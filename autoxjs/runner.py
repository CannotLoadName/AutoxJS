#-*-coding:utf-8;-*-
from errno import EISDIR,ENOENT
from json import dumps,load
from os.path import abspath,dirname,exists,expandvars,isfile,join
from random import randrange
from socket import SocketType,socket
from subprocess import run
from tempfile import NamedTemporaryFile
from time import time_ns
from typing import Any,Iterable,Optional
from urllib.parse import quote,urlunsplit
from .compressor import compressScript
MODULE_PATH=dirname(__spec__.origin)
CONFIG=load(open(join(MODULE_PATH,"config.json"),"r",encoding="utf-8"))
AUTO_RUNNER=compressScript(open(join(MODULE_PATH,"autorunner.js"),"r",encoding="utf-8"))
FILE_RUNNER=compressScript(open(join(MODULE_PATH,"filerunner.js"),"r",encoding="utf-8"))
STRING_RUNNER=compressScript(open(join(MODULE_PATH,"stringrunner.js"),"r",encoding="utf-8"))
FORCE_STOP=compressScript(open(join(MODULE_PATH,"forcestop.js"),"r",encoding="utf-8"))
def bindAvailablePort(unboundSocket:SocketType,listenBacklog:Optional[int]=None,connectAddress:Any=None)->int:
    portsCount=CONFIG["max_port"]+1-CONFIG["min_port"]
    portBase=randrange(portsCount)
    for i in range(portBase,portsCount+portBase):
        port=i%portsCount+CONFIG["min_port"]
        address=(CONFIG["host_name"],port)
        try:
            unboundSocket.bind(address)
        except OSError:
            pass
        else:
            break
    else:
        raise OverflowError("No available ports found")
    if connectAddress is None:
        if listenBacklog is not None:
            unboundSocket.listen(int(listenBacklog))
    else:
        unboundSocket.connect(connectAddress)
    return port
def runAutoFile(filePath:str)->str:
    absolutePath=abspath(str(filePath))
    if not exists(absolutePath):
        raise FileNotFoundError(ENOENT,"The file doesn't exist",filePath)
    if not isfile(absolutePath):
        raise IsADirectoryError(EISDIR,"The path belongs to a directory",filePath)
    with socket() as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(AUTO_RUNNER%(CONFIG["script_host_name"],serverPort))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                clientSocket.sendall((dumps({"file":absolutePath,"path":dirname(absolutePath)},ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))
    return absolutePath
def runFile(filePath:str)->str:
    absolutePath=abspath(str(filePath))
    if not exists(absolutePath):
        raise FileNotFoundError(ENOENT,"The file doesn't exist",filePath)
    if not isfile(absolutePath):
        raise IsADirectoryError(EISDIR,"The path belongs to a directory",filePath)
    with socket() as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(FILE_RUNNER%(CONFIG["script_host_name"],serverPort))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                clientSocket.sendall((dumps({"file":absolutePath,"path":dirname(absolutePath)},ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))
    return absolutePath
def runString(commandString:str,commandTitle:Optional[str]=None)->str:
    with socket() as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(STRING_RUNNER%(CONFIG["script_host_name"],serverPort))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                if commandTitle is None:
                    usedTitle="%s-%d"%(CONFIG["command_title"],time_ns())
                else:
                    usedTitle=str(commandTitle)
                clientSocket.sendall((dumps({"name":usedTitle,"script":str(commandString)},ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))
    return usedTitle
def forceStop(sources:Iterable[str],addSuffix:bool=False)->None:
    usedSources=[]
    for i in sources:
        if addSuffix:
            usedSources.append(str(i)+CONFIG["force_stop_suffix"])
        else:
            usedSources.append(str(i))
    with socket() as serverSocket:
        serverPort=bindAvailablePort(serverSocket,1)
        with NamedTemporaryFile("w",encoding="utf-8",suffix=CONFIG["temporary_file_suffix"],dir=abspath(expandvars(CONFIG["temporary_path"]))) as tempFile:
            tempFile.write(FORCE_STOP%(CONFIG["script_host_name"],serverPort))
            tempFile.flush()
            run((expandvars(CONFIG["am_command"]),CONFIG["am_subcommand"],"--user",CONFIG["am_user"],"-a",CONFIG["intent_action"],"-d",urlunsplit((CONFIG["url_scheme"],"",quote(tempFile.name,encoding="utf-8"),"","")),"-t",CONFIG["intent_mime_type"],"--grant-read-uri-permission","--grant-write-uri-permission","--grant-prefix-uri-permission","--include-stopped-packages","--activity-exclude-from-recents","--activity-no-animation",CONFIG["intent_component"]),check=True)
            with serverSocket.accept()[0] as clientSocket:
                clientSocket.sendall((dumps({"sources":usedSources},ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))