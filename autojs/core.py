# -*-coding:utf-8;-*-
from json import dumps
from os import getenv
from os.path import abspath, dirname, exists, isfile, join
from socket import AF_INET, SOCK_STREAM, socket
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import TextIO, Tuple
from urllib.parse import quote


def createSocket() -> Tuple[socket, int]:
    oServer = socket(AF_INET, SOCK_STREAM)
    oPort = 49152
    while True:
        oPair = ("localhost", oPort)
        try:
            oServer.bind(oPair)
        except Exception:
            if oPort < 65535:
                oPort += 1
            else:
                oServer.close()
                raise OverflowError("No available ports found.")
        else:
            break
    oServer.listen(1)
    return oServer, oPort


def createTempFile(isString: bool, iPort: int) -> TextIO:
    oPath = abspath(getenv("EXTERNAL_STORAGE", "/sdcard"))
    try:
        oFile = NamedTemporaryFile("w", encoding="utf-8", suffix=".js", dir=oPath, errors="ignore")
    except Exception:
        raise PermissionError("Termux doesn't have the write permission of the external storage.")
    if isString:
        oFile.write(
            open(join(dirname(__file__), "string_runner.js"), "r", encoding="utf-8", errors="ignore").read() % (iPort,))
    else:
        oFile.write(
            open(join(dirname(__file__), "file_runner.js"), "r", encoding="utf-8", errors="ignore").read() % (iPort,))
    oFile.flush()
    return oFile


def runTempFile(iPath: str) -> None:
    oCommand = (
        "am", "start", "-W", "-a", "VIEW", "-d", "file://%s" % (quote(iPath, encoding="utf-8", errors="ignore"),), "-t",
        "application/x-javascript", "--grant-read-uri-permission", "--grant-write-uri-permission",
        "--grant-prefix-uri-permission", "--include-stopped-packages", "--activity-exclude-from-recents",
        "--activity-no-animation", "org.autojs.autojs/.external.open.RunIntentActivity")
    try:
        oReturn = run(oCommand)
    except Exception as oError:
        raise ChildProcessError(
            "Unable to launch Auto.js or Autox.js application. The reason is a %s." % (type(oError).__name__,))
    if oReturn.returncode != 0:
        raise ChildProcessError(
            "Unable to launch Auto.js or Autox.js application. The return code is %d." % (oReturn.returncode,))


def sendCommand(isString: bool, iServer: socket, iStringOrFile: str, iTitleOrPath: str) -> None:
    oClient, oPair = iServer.accept()
    if isString:
        oBytes = (dumps({"name": iTitleOrPath, "script": iStringOrFile}, ensure_ascii=False,
                        separators=(",", ":")) + "\n").encode("utf-8", "ignore")
    else:
        oBytes = (dumps({"file": iStringOrFile, "path": iTitleOrPath}, ensure_ascii=False,
                        separators=(",", ":")) + "\n").encode("utf-8", "ignore")
    try:
        oClient.sendall(oBytes)
    except Exception:
        oClient.close()
        raise BrokenPipeError("Failed while sending command to the client program.")
    oClient.close()


def runFile(iPath: str) -> None:
    if type(iPath) != str:
        raise TypeError("The path of script must be a string.")
    oPath = abspath(iPath)
    if not (exists(oPath) and isfile(oPath)):
        raise FileNotFoundError("The script must be an existing file.")
    oServer, oPort = createSocket()
    try:
        oTempFile = createTempFile(False, oPort)
    except PermissionError as oError:
        oServer.close()
        raise oError
    try:
        runTempFile(oTempFile.name)
    except ChildProcessError as oError:
        oServer.close()
        oTempFile.close()
        raise oError
    try:
        sendCommand(False, oServer, oPath, dirname(oPath))
    except BrokenPipeError as oError:
        oServer.close()
        oTempFile.close()
        raise oError
    oServer.close()
    oTempFile.close()


def runString(iString: str, iTitle: str = "Script") -> None:
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
    try:
        runTempFile(oTempFile.name)
    except ChildProcessError as oError:
        oServer.close()
        oTempFile.close()
        raise oError
    try:
        sendCommand(True, oServer, iString, iTitle)
    except BrokenPipeError as oError:
        oServer.close()
        oTempFile.close()
        raise oError
    oServer.close()
    oTempFile.close()
