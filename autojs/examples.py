# -*-coding:utf-8;-*-
from array import array
from json import dumps, loads
from os.path import dirname, join
from socket import socket
from threading import Lock, Thread
from time import time_ns
from typing import Callable, Dict, List, Tuple, Union
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


def threadMain(lockRead: Lock, lockCallback: Lock, lockEnd: Lock, result: dict, callback: List[Callable[[dict], None]],
               endCallback: List[Callable[[], None]], iClient: socket) -> None:
    oFileDescriptor = iClient.makefile("r", encoding="utf-8", errors="ignore")
    while True:
        try:
            oInputLine = oFileDescriptor.readline()
        except Exception:
            break
        else:
            if oInputLine != "" and oInputLine[-1] == "\n":
                try:
                    oInputDict = loads(oInputLine)
                except Exception:
                    break
                else:
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
                                warn("A callback function raised a %s with the description \"%s\" ." % (
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
                warn("A callback function raised a %s with the description \"%s\" ." % (
                    type(oError).__name__, oError.args[0]))
    lockEnd.release()
    oFileDescriptor.close()
    iClient.close()


def recorderThreadMain(lockRead: Lock, lockCallback: Lock, lockEnd: Lock, result: Dict[str, Union[bytes, int]],
                       callback: List[Callable[[array], None]], endCallback: List[Callable[[], None]],
                       iClient: socket) -> None:
    oLastEndByte = b""
    while True:
        try:
            oInputBytes = iClient.recv(65536)
        except Exception:
            break
        else:
            if oInputBytes == b"":
                break
            else:
                oInputBytes = oLastEndByte + oInputBytes
                if len(oInputBytes) % 2 == 0:
                    oLastEndByte = b""
                else:
                    oLastEndByte = oInputBytes[-1]
                    oInputBytes = oInputBytes[0:-1]
                lockRead.acquire()
                result["data"] = oInputBytes
                if "serial_number" in result:
                    result["serial_number"] += 1
                else:
                    result["serial_number"] = 0
                lockRead.release()
                lockCallback.acquire()
                for i in callback:
                    oInputBytesTemp = array("h", oInputBytes)
                    try:
                        i(oInputBytesTemp)
                    except Exception as oError:
                        if len(oError.args) == 0:
                            warn("A callback function raised a %s." % (type(oError).__name__,))
                        else:
                            warn("A callback function raised a %s with the description \"%s\" ." % (
                                type(oError).__name__, oError.args[0]))
                lockCallback.release()
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
                warn("A callback function raised a %s with the description \"%s\" ." % (
                    type(oError).__name__, oError.args[0]))
    lockEnd.release()
    iClient.close()


class LocatorRecorderOrSensor:
    _lockMain: Lock
    _lockRead: Lock
    _lockCallback: Lock
    _lockEndCallback: Lock
    _result: dict
    _callback: List[Callable[[Union[dict, array]], None]]
    _endCallback: List[Callable[[], None]]
    _client: Union[socket, None]

    def __init__(self) -> None:
        self._lockMain = Lock()
        self._lockRead = Lock()
        self._lockCallback = Lock()
        self._lockEndCallback = Lock()
        self._result = {}
        self._callback = []
        self._endCallback = []
        self._client = None

    def __del__(self) -> None:
        if self._client is not None:
            oClientTemp = self._client
            try:
                oClientTemp.send(b"{}\n")
            except Exception:
                pass

    def callback(self, iCallback: Callable[[Union[dict, array]], None]) -> None:
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockCallback.acquire()
        self._callback.append(iCallback)
        self._lockCallback.release()

    def clearCallbacks(self) -> None:
        self._lockCallback.acquire()
        self._callback.clear()
        self._lockCallback.release()

    def endCallback(self, iCallback: Callable[[], None]) -> None:
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockEndCallback.acquire()
        self._endCallback.append(iCallback)
        self._lockEndCallback.release()

    def clearEndCallbacks(self) -> None:
        self._lockEndCallback.acquire()
        self._endCallback.clear()
        self._lockEndCallback.release()

    def stop(self) -> None:
        self._lockMain.acquire()
        if self._client is None:
            self._lockMain.release()
            raise AttributeError("The locator, recorder or sensor has already been stopped.")
        oClientTemp = self._client
        try:
            oClientTemp.send(b"{}\n")
        except Exception:
            pass
        self._client = None
        self._lockMain.release()


class Location(LocatorRecorderOrSensor):
    @staticmethod
    def requestPermission() -> None:
        runString("runtime.requestPermissions([\"access_fine_location\"]);", "LocatingPermission-%d" % (time_ns(),))

    def start(self, iProvider: str, iDelay: int = 1000) -> None:
        if type(iProvider) != str:
            raise TypeError("The location provider must be a string.")
        if type(iDelay) != int:
            raise TypeError("The delay of locator must be an integer.")
        if iProvider not in LOCATION_PROVIDERS:
            raise ValueError("Unsupported location provider.")
        if iDelay < 0 or iDelay > 2147483647:
            raise ValueError("The delay of locator must be between 0 and 2147483647 milliseconds.")
        self._lockMain.acquire()
        if self._client is not None:
            self._lockMain.release()
            raise AttributeError("The locator has already been started.")
        try:
            oServer, oPort = createSocket()
        except OverflowError as oError:
            self._lockMain.release()
            raise oError
        oScriptString = open(join(dirname(__file__), "locator_caller.js"), "r", encoding="utf-8",
                             errors="ignore").read() % (oPort,)
        oScriptTitle = "LocationManager-%d" % (time_ns(),)
        try:
            runString(oScriptString, oScriptTitle)
        except (OverflowError, PermissionError, ChildProcessError, BrokenPipeError) as oError:
            self._lockMain.release()
            oServer.close()
            raise oError
        oClient, oPair = oServer.accept()
        oBytes = (dumps({"provider": iProvider, "delay": iDelay, "distance": 0}, ensure_ascii=False,
                        separators=(",", ":")) + "\n").encode("utf-8", "ignore")
        try:
            oClient.sendall(oBytes)
        except Exception:
            self._lockMain.release()
            oClient.close()
            oServer.close()
            raise BrokenPipeError("Failed while sending arguments to the client program.")
        Thread(target=threadMain, args=(
            self._lockRead, self._lockCallback, self._lockEndCallback, self._result, self._callback, self._endCallback,
            oClient)).start()
        self._client = oClient
        self._lockMain.release()
        oServer.close()

    def read(self) -> dict:
        self._lockRead.acquire()
        oResult = copyDict(self._result)
        self._lockRead.release()
        return oResult


class Recorder(LocatorRecorderOrSensor):
    @staticmethod
    def requestPermission() -> None:
        runString("runtime.requestPermissions([\"record_audio\"]);", "RecordingPermission-%d" % (time_ns(),))

    def start(self) -> None:
        self._lockMain.acquire()
        if self._client is not None:
            self._lockMain.release()
            raise AttributeError("The recorder has already been started.")
        try:
            oServer, oPort = createSocket()
        except OverflowError as oError:
            self._lockMain.release()
            raise oError
        oScriptString = open(join(dirname(__file__), "recorder_caller.js"), "r", encoding="utf-8",
                             errors="ignore").read() % (oPort,)
        oScriptTitle = "AudioRecorder-%d" % (time_ns(),)
        try:
            runString(oScriptString, oScriptTitle)
        except (OverflowError, PermissionError, ChildProcessError, BrokenPipeError) as oError:
            self._lockMain.release()
            oServer.close()
            raise oError
        oClient, oPair = oServer.accept()
        oBytes = (dumps({"samplerate": 44100, "channel": "mono", "format": "16bit"}, ensure_ascii=False,
                        separators=(",", ":")) + "\n").encode("utf-8", "ignore")
        try:
            oClient.sendall(oBytes)
        except Exception:
            self._lockMain.release()
            oClient.close()
            oServer.close()
            raise BrokenPipeError("Failed while sending arguments to the client program.")
        Thread(target=recorderThreadMain, args=(
            self._lockRead, self._lockCallback, self._lockEndCallback, self._result, self._callback, self._endCallback,
            oClient)).start()
        self._client = oClient
        self._lockMain.release()
        oServer.close()

    def read(self) -> Tuple[int, Union[array, None]]:
        self._lockRead.acquire()
        if len(self._result) == 0:
            self._lockRead.release()
            return -1, None
        else:
            oSerialNumber = self._result["serial_number"]
            oData = array("h", self._result["data"])
            self._lockRead.release()
            return oSerialNumber, oData


class Sensor(LocatorRecorderOrSensor):
    def start(self, iType: str, iDelay: int = 3) -> None:
        if type(iType) != str:
            raise TypeError("The type of sensor must be a string.")
        if type(iDelay) != int:
            raise TypeError("The delay of sensor must be an integer.")
        if iType not in SENSOR_TYPES:
            raise ValueError("Unsupported type of sensor.")
        if iDelay < 0 or iDelay > 2147483647:
            raise ValueError("The delay of sensor must be between 0 and 2147483647 microseconds.")
        self._lockMain.acquire()
        if self._client is not None:
            self._lockMain.release()
            raise AttributeError("The sensor has already been started.")
        try:
            oServer, oPort = createSocket()
        except OverflowError as oError:
            self._lockMain.release()
            raise oError
        oScriptString = open(join(dirname(__file__), "sensor_caller.js"), "r", encoding="utf-8",
                             errors="ignore").read() % (oPort,)
        oScriptTitle = "SensorManager-%d" % (time_ns(),)
        try:
            runString(oScriptString, oScriptTitle)
        except (OverflowError, PermissionError, ChildProcessError, BrokenPipeError) as oError:
            self._lockMain.release()
            oServer.close()
            raise oError
        oClient, oPair = oServer.accept()
        oBytes = (dumps({"type": iType, "delay": iDelay}, ensure_ascii=False, separators=(",", ":")) + "\n").encode(
            "utf-8", "ignore")
        try:
            oClient.sendall(oBytes)
        except Exception:
            self._lockMain.release()
            oClient.close()
            oServer.close()
            raise BrokenPipeError("Failed while sending arguments to the client program.")
        Thread(target=threadMain, args=(
            self._lockRead, self._lockCallback, self._lockEndCallback, self._result, self._callback, self._endCallback,
            oClient)).start()
        self._client = oClient
        self._lockMain.release()
        oServer.close()

    def read(self) -> dict:
        self._lockRead.acquire()
        oResult = copyDict(self._result)
        self._lockRead.release()
        return oResult
