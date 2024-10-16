# -*-coding:utf-8;-*-
from io import StringIO
from json import dumps
from os import getenv
from os.path import abspath, dirname, exists, isfile, join
from socket import socket, AF_INET, SOCK_STREAM
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Tuple


def createSocket() -> Tuple[socket, int]:
    oServer = socket(AF_INET, SOCK_STREAM)
    oPort = 16384
    while True:
        oAddressTemp = ("localhost", oPort)
        try:
            oServer.bind(oAddressTemp)
        except Exception:
            oPort += 1
        else:
            break
    oServer.listen(1)
    return oServer, oPort


def createTempFile(isString: bool, iPort: int) -> StringIO:
    oPath = abspath(getenv("EXTERNAL_STORAGE", "/sdcard"))
    try:
        oFile = NamedTemporaryFile("w", encoding="utf-8", suffix=".js", dir=oPath)
    except Exception:
        raise PermissionError("Termux doesn't have the write permission of external storage.")
    if isString:
        oFile.write(open(join(dirname(__file__), "execute_string.js"), "r", encoding="utf-8").read() % (iPort,))
    else:
        oFile.write(open(join(dirname(__file__), "execute_file.js"), "r", encoding="utf-8").read() % (iPort,))
    oFile.flush()
    return oFile


def runTempFile(iFile: str) -> bool:
    return run(("am", "start", "-W", "-a", "android.intent.action.VIEW", "-d", "file://%s" % (iFile,), "-t",
                "application/x-javascript", "--grant-read-uri-permission", "--grant-write-uri-permission",
                "--grant-prefix-uri-permission", "--include-stopped-packages", "--activity-exclude-from-recents",
                "--activity-no-animation", "org.autojs.autojs/.external.open.RunIntentActivity")).returncode == 0


def sendScript(isString: bool, iServer: socket, iStringOrFile: str, iTitleOrPath: str):
    oClient, oAddress = iServer.accept()
    if isString:
        oClient.send((dumps({"name": iTitleOrPath, "script": iStringOrFile}, ensure_ascii=False,
                            separators=(",", ":")) + "\n").encode("utf-8"))
    else:
        oClient.send((dumps({"file": iStringOrFile, "path": iTitleOrPath}, ensure_ascii=False,
                            separators=(",", ":")) + "\n").encode("utf-8"))
    oClient.close()


def runFile(iFile: str) -> bool:
    if type(iFile) != str:
        raise TypeError("The path of script must be a string.")
    oFile = abspath(iFile)
    if not (exists(oFile) and isfile(oFile)):
        raise FileNotFoundError("The script must be an existing file.")
    oServer, oPort = createSocket()
    try:
        oTempFile = createTempFile(False, oPort)
    except PermissionError as oError:
        oServer.close()
        raise oError
    if runTempFile(oTempFile.name):
        sendScript(False, oServer, oFile, dirname(oFile))
        oServer.close()
        oTempFile.close()
        return True
    else:
        oServer.close()
        oTempFile.close()
        return False


def runString(iString: str, iTitle: str = "script") -> bool:
    if type(iString) != str:
        raise TypeError("The script must be a string.")
    if type(iTitle) != str:
        raise TypeError("The name of script must be a string.")
    if iTitle == "":
        raise ValueError("The name of script shouldn't be void.")
    oServer, oPort = createSocket()
    try:
        oTempFile = createTempFile(True, oPort)
    except PermissionError as oError:
        oServer.close()
        raise oError
    if runTempFile(oTempFile.name):
        sendScript(True, oServer, iString, iTitle)
        oServer.close()
        oTempFile.close()
        return True
    else:
        oServer.close()
        oTempFile.close()
        return False
