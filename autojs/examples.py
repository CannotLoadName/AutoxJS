# -*-coding:utf-8;-*-
from json import dumps, loads
from os.path import dirname, join
from socket import socket
from threading import Lock, Thread
from time import time_ns
from typing import Callable, List, Union
from warnings import warn
from .core import createSocket, runString

LOCATION_PROVIDERS = ("gps", "network")
SENSOR_TYPES = (
    "accelerometer", "gravity", "gyroscope", "light", "linear_acceleration", "magnetic_field", "orientation",
    "proximity",
    "rotation_vector", "step_counter")


def copyList(iList: list) -> list:
    oList = []
    for i in iList:
        if type(i) == list:
            oList.append(copyList(i))
        elif type(i) == dict:
            oList.append(copyDict(i))
        else:
            oList.append(i)
    return oList


def copyDict(iDict: dict) -> dict:
    oDict = {}
    for i in iDict:
        if type(iDict[i]) == dict:
            oDict[i] = copyDict(iDict[i])
        elif type(iDict[i]) == list:
            oDict[i] = copyList(iDict[i])
        else:
            oDict[i] = iDict[i]
    return oDict


def threadMain(lockRead: Lock, lockCallback: Lock, lockEnd: Lock, result: dict, callback: List[Callable],
               endCallback: List[Callable], iClient: socket, args: dict):
    oFileDescriptor = iClient.makefile("r", encoding="utf-8")
    iClient.send((dumps(args, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    while True:
        oInputLine = oFileDescriptor.readline()
        if oInputLine != "" and oInputLine[-1] == "\n":
            oInputDict = loads(oInputLine)
            lockRead.acquire()
            for i in oInputDict:
                result[i] = oInputDict[i]
            lockRead.release()
            lockCallback.acquire()
            for i in callback:
                oInputDictTemp = copyDict(oInputDict)
                try:
                    i(oInputDictTemp)
                except Exception as oError:
                    if len(oError.args) == 0:
                        warn("A callback function raised a %s." % (type(oError).__name__,))
                    else:
                        warn("A callback function raised a %s with description \"%s\" ." % (
                            type(oError).__name__, oError.args[0]))
            lockCallback.release()
        else:
            break
    lockRead.acquire()
    result.clear()
    lockRead.release()
    lockEnd.acquire()
    for i in endCallback:
        try:
            i()
        except Exception as oError:
            if len(oError.args) == 0:
                warn("A callback function raised a %s." % (type(oError).__name__,))
            else:
                warn("A callback function raised a %s with description \"%s\" ." % (
                    type(oError).__name__, oError.args[0]))
    lockEnd.release()
    oFileDescriptor.close()
    iClient.close()


class LocatorOrSensor:
    _lockMain: Union[Lock, None] = None
    _lockRead: Union[Lock, None] = None
    _lockCallback: Union[Lock, None] = None
    _lockEndCallback: Union[Lock, None] = None
    _result: Union[dict, None] = None
    _callback: Union[List[Callable], None] = None
    _endCallback: Union[List[Callable], None] = None
    _client: Union[socket, None] = None

    def __init__(self):
        self._lockMain = Lock()
        self._lockRead = Lock()
        self._lockCallback = Lock()
        self._lockEndCallback = Lock()
        self._result = {}
        self._callback = []
        self._endCallback = []

    def __del__(self):
        self._lockMain.acquire()
        if self._client is not None:
            oClientTemp = self._client
            try:
                oClientTemp.send(b"{}\n")
            except Exception:
                pass
            self._client = None
        self._lockMain.release()

    def callback(self, iCallback: Callable):
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockCallback.acquire()
        self._callback.append(iCallback)
        self._lockCallback.release()

    def clearCallbacks(self):
        self._lockCallback.acquire()
        self._callback.clear()
        self._lockCallback.release()

    def endCallback(self, iCallback: Callable):
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockEndCallback.acquire()
        self._endCallback.append(iCallback)
        self._lockEndCallback.release()

    def clearEndCallbacks(self):
        self._lockEndCallback.acquire()
        self._endCallback.clear()
        self._lockEndCallback.release()

    def read(self) -> dict:
        self._lockRead.acquire()
        oResult = copyDict(self._result)
        self._lockRead.release()
        return oResult

    def stop(self):
        self._lockMain.acquire()
        if self._client is None:
            self._lockMain.release()
            raise AttributeError("The locator or sensor has already been stopped.")
        oClientTemp = self._client
        try:
            oClientTemp.send(b"{}\n")
        except Exception:
            pass
        self._client = None
        self._lockMain.release()


class Location(LocatorOrSensor):
    def start(self, iProvider: str, iDelay: int = 1000):
        if type(iProvider) != str:
            raise TypeError("The location provider must be a string.")
        if type(iDelay) != int:
            raise TypeError("The delay of locator must be an integer.")
        if iProvider not in LOCATION_PROVIDERS:
            raise ValueError("Unsupported location provider.")
        if iDelay < 1 or iDelay > 2147483:
            raise ValueError("The delay of locator must be between 1 and 2147483 milliseconds.")
        self._lockMain.acquire()
        if self._client is not None:
            self._lockMain.release()
            raise AttributeError("The locator has already been started.")
        oServer, oPort = createSocket()
        oScriptString = open(join(dirname(__file__), "call_locator.js"), "r", encoding="utf-8").read() % (oPort,)
        oScriptTitle = "LocationManager%d" % (time_ns(),)
        try:
            isRunSuccess = runString(oScriptString, oScriptTitle)
        except PermissionError as oError:
            self._lockMain.release()
            oServer.close()
            raise oError
        if isRunSuccess:
            self._client, oAddress = oServer.accept()
            Thread(target=threadMain, args=(
                self._lockRead, self._lockCallback, self._lockEndCallback, self._result, self._callback,
                self._endCallback,
                self._client, {"provider": iProvider, "delay": iDelay})).start()
            self._lockMain.release()
            oServer.close()
        else:
            self._lockMain.release()
            oServer.close()
            raise ChildProcessError("Unable to launch Auto.js or Autox.js application.")


class Sensor(LocatorOrSensor):
    def start(self, iType: str, iDelay: int = 200):
        if type(iType) != str:
            raise TypeError("The type of sensor must be a string.")
        if type(iDelay) != int:
            raise TypeError("The delay of sensor must be an integer.")
        if iType not in SENSOR_TYPES:
            raise ValueError("Unsupported type of sensor.")
        if iDelay < 1 or iDelay > 2147483:
            raise ValueError("The delay of sensor must be between 1 and 2147483 milliseconds.")
        self._lockMain.acquire()
        if self._client is not None:
            self._lockMain.release()
            raise AttributeError("The sensor has already been started.")
        oServer, oPort = createSocket()
        oScriptString = open(join(dirname(__file__), "call_sensors.js"), "r", encoding="utf-8").read() % (oPort,)
        oScriptTitle = "SensorManager%d" % (time_ns(),)
        try:
            isRunSuccess = runString(oScriptString, oScriptTitle)
        except PermissionError as oError:
            self._lockMain.release()
            oServer.close()
            raise oError
        if isRunSuccess:
            self._client, oAddress = oServer.accept()
            Thread(target=threadMain, args=(
                self._lockRead, self._lockCallback, self._lockEndCallback, self._result, self._callback,
                self._endCallback,
                self._client, {"type": iType, "delay": iDelay})).start()
            self._lockMain.release()
            oServer.close()
        else:
            self._lockMain.release()
            oServer.close()
            raise ChildProcessError("Unable to launch Auto.js or Autox.js application.")
