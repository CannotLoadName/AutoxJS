from os import getenv, remove, listdir, mkdir, rmdir
from os.path import normpath, join, split, exists, isfile, commonpath
from time import time_ns
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import run
from json import dumps

stringLoader = """var socket=new java.net.Socket("localhost",%d);
var in_byte=socket.getInputStream();
var in_char=new java.io.InputStreamReader(in_byte,"utf-8");
var in_buf=new java.io.BufferedReader(in_char);
var in_json=JSON.parse(in_buf.readLine());
in_buf.close();
in_char.close();
in_byte.close();
engines.execScript(in_json.title,in_json.script);
socket.close();
"""
fileLoader = """var socket=new java.net.Socket("localhost",%d);
var in_byte=socket.getInputStream();
var in_char=new java.io.InputStreamReader(in_byte,"utf-8");
var in_buf=new java.io.BufferedReader(in_char);
var in_json=JSON.parse(in_buf.readLine());
in_buf.close();
in_char.close();
in_byte.close();
engines.execScriptFile(in_json.file,{path:in_json.directory});
socket.close();
"""
basePath = normpath(getenv("EXTERNAL_STORAGE", "/sdcard"))
tempPath = join(basePath, normpath("Android/data/com.termux/cache"))


def getServer():
    fSocket = socket(AF_INET, SOCK_STREAM)
    fPort = 16384
    while True:
        try:
            fSocket.bind(("localhost", fPort))
        except Exception:
            fPort += 1
        else:
            break
    fSocket.listen(1)
    return fSocket, fPort


def createTempDirs(iPath):
    if iPath != basePath:
        createTempDirs(split(iPath)[0])
        if not exists(iPath):
            mkdir(iPath)


def createTempFile(isScript, iPort):
    createTempDirs(tempPath)
    fName = join(tempPath, ".%d.js.tmp" % (time_ns(),))
    fd = open(fName, "w")
    if isScript:
        fd.write(stringLoader % (iPort,))
    else:
        fd.write(fileLoader % (iPort,))
    fd.close()
    return fName


def privateRunFile(iFile):
    return run(("am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", "file://%s" % (iFile,), "-t",
                "application/x-javascript", "--grant-read-uri-permission", "--grant-prefix-uri-permission",
                "--include-stopped-packages", "--activity-no-animation",
                "org.autojs.autojs/.external.open.RunIntentActivity")).returncode == 0


def sendString(isScript, iSocket, iScript, iTitle):
    fSocket, addr = iSocket.accept()
    if isScript:
        fSocket.send((dumps({"title": iTitle, "script": iScript}) + "\n").encode("utf-8"))
    else:
        fSocket.send((dumps({"file": iScript, "directory": iTitle}) + "\n").encode("utf-8"))
    fSocket.recv(1)
    fSocket.close()


def removeTempFile(iFile):
    remove(iFile)
    if len(listdir(tempPath)) == 0:
        rmdir(tempPath)


def runString(iScript: str, iTitle: str):
    if type(iScript) != str:
        raise TypeError("The script must be a string.")
    if type(iTitle) != str:
        raise TypeError("The name of script must be a string.")
    if iTitle == "":
        raise ValueError("The name of script shouldn't be void.")
    fServer, fPort = getServer()
    fTempFile = createTempFile(True, fPort)
    if privateRunFile(fTempFile):
        sendString(True, fServer, iScript, iTitle)
        fServer.close()
        removeTempFile(fTempFile)
        return True
    else:
        fServer.close()
        removeTempFile(fTempFile)
        return False


def runFile(iFile: str):
    if type(iFile) != str:
        raise TypeError("The path of script must be a string.")
    fFile = normpath(iFile)
    if not (exists(fFile) and isfile(fFile)):
        raise OSError("The script must be an existing file.")
    if commonpath((fFile, basePath)) != basePath:
        raise OSError("The script must be in external storage.")
    fServer, fPort = getServer()
    fTempFile = createTempFile(False, fPort)
    if privateRunFile(fTempFile):
        sendString(False, fServer, fFile, split(fFile)[0])
        fServer.close()
        removeTempFile(fTempFile)
        return True
    else:
        fServer.close()
        removeTempFile(fTempFile)
        return False
