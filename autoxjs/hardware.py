#-*-coding:utf-8;-*-
from array import ArrayType,array
from copy import deepcopy
from json import dumps,loads
from os.path import dirname,join
from socket import SocketType,socket
from threading import Lock,Thread
from time import time_ns
from typing import Any,Callable,Dict,List,Optional,Tuple,Union
from warnings import warn
from .compressor import compressScript
from .runner import CONFIG,bindAvailablePort,runString
from .remotecaller import Context
MODULE_PATH=dirname(__spec__.origin)
LOCATOR_SCRIPT=compressScript(open(join(MODULE_PATH,"locator.js"),"r",encoding="utf-8"))
RECORDER_SCRIPT=compressScript(open(join(MODULE_PATH,"recorder.js"),"r",encoding="utf-8"))
SENSOR_SCRIPT=compressScript(open(join(MODULE_PATH,"sensor.js"),"r",encoding="utf-8"))
def locatorAndSensorMain(readLock:Lock,callbackLock:Lock,endCallbackLock:Lock,result:Dict[str,Union[Dict[str,Any],int]],callback:List[Callable[[Dict[str,Any]],None]],endCallback:List[Callable[[],None]],tempSocket:SocketType,arguments:Dict[str,Union[float,int,str]])->None:
    tempCallback=[]
    with tempSocket as clientSocket:
        clientSocket.sendall((dumps(arguments,ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))
        with clientSocket.makefile("r",encoding="utf-8") as socketReader:
            while True:
                try:
                    inputLine=socketReader.readline()
                except OSError:
                    break
                else:
                    if inputLine.endswith("\n"):
                        inputDict=loads(inputLine)
                        with readLock:
                            result["data"]=inputDict
                            if "serial_number" in result:
                                result["serial_number"]+=1
                            else:
                                result["serial_number"]=0
                        with callbackLock:
                            tempCallback.extend(callback)
                        for i in tempCallback:
                            tempDict=deepcopy(inputDict)
                            try:
                                i(tempDict)
                            except Exception as error:
                                warn("A callback function raised a %s: %s"%(type(error).__name__,str(error)))
                        tempCallback.clear()
                    else:
                        break
    with readLock:
        result.clear()
    with endCallbackLock:
        tempCallback.extend(endCallback)
    for i in tempCallback:
        try:
            i()
        except Exception as error:
            warn("An end callback function raised a %s: %s"%(type(error).__name__,str(error)))
def recorderMain(readLock:Lock,callbackLock:Lock,endCallbackLock:Lock,result:Dict[str,Union[bytes,int]],callback:List[Callable[[ArrayType],None]],endCallback:List[Callable[[],None]],tempSocket:SocketType,receiveSize:int,itemSize:int,typeCode:str,arguments:Dict[str,Union[float,int,str]])->None:
    tempCallback=[]
    with tempSocket as clientSocket:
        clientSocket.sendall((dumps(arguments,ensure_ascii=False,allow_nan=False,separators=(",",":"))+"\n").encode("utf-8"))
        lastLength=0
        with memoryview(bytearray(receiveSize+itemSize-1)) as inputBuffer:
            while True:
                tempBuffer=inputBuffer[lastLength:receiveSize+lastLength]
                try:
                    inputLength=clientSocket.recv_into(tempBuffer,receiveSize)
                except OSError:
                    break
                else:
                    if inputLength>0:
                        totalLength=inputLength+lastLength
                        lastLength=totalLength%itemSize
                        usedLength=totalLength-lastLength
                        if usedLength>0:
                            inputBytes=inputBuffer[:usedLength].tobytes()
                            with readLock:
                                result["data"]=inputBytes
                                if "serial_number" in result:
                                    result["serial_number"]+=1
                                else:
                                    result["serial_number"]=0
                            with callbackLock:
                                tempCallback.extend(callback)
                            for i in tempCallback:
                                inputArray=array(typeCode,inputBytes)
                                try:
                                    i(inputArray)
                                except Exception as error:
                                    warn("A callback function raised a %s: %s"%(type(error).__name__,str(error)))
                            tempCallback.clear()
                            inputBuffer[:lastLength]=inputBuffer[usedLength:totalLength]
                    else:
                        break
    with readLock:
        result.clear()
    with endCallbackLock:
        tempCallback.extend(endCallback)
    for i in tempCallback:
        try:
            i()
        except Exception as error:
            warn("An end callback function raised a %s: %s"%(type(error).__name__,str(error)))
class LocatorRecorderOrSensor:
    _mainLock:Lock
    _readLock:Lock
    _callbackLock:Lock
    _endCallbackLock:Lock
    _result:Dict[str,Union[Dict[str,Any],bytes,int]]
    _callback:List[Callable[[Union[ArrayType,Dict[str,Any]]],None]]
    _endCallback:List[Callable[[],None]]
    _clientSocket:Optional[SocketType]
    def __init__(self)->None:
        self._mainLock=Lock()
        self._readLock=Lock()
        self._callbackLock=Lock()
        self._endCallbackLock=Lock()
        self._result={}
        self._callback=[]
        self._endCallback=[]
        self._clientSocket=None
    def __del__(self)->None:
        tempSocket=self._clientSocket
        if tempSocket is not None:
            try:
                tempSocket.sendall(b"{}\n")
            except OSError:
                pass
    def addCallback(self,callback:Callable[[Union[ArrayType,Dict[str,Any]]],None])->Callable[[Union[ArrayType,Dict[str,Any]]],None]:
        with self._callbackLock:
            self._callback.append(callback)
        return callback
    def clearCallbacks(self)->None:
        with self._callbackLock:
            self._callback.clear()
    def addEndCallback(self,endCallback:Callable[[],None])->Callable[[],None]:
        with self._endCallbackLock:
            self._endCallback.append(endCallback)
        return endCallback
    def clearEndCallbacks(self)->None:
        with self._endCallbackLock:
            self._endCallback.clear()
    def stop(self)->None:
        with self._mainLock:
            tempSocket=self._clientSocket
            if tempSocket is None:
                raise AttributeError("The locator, recorder or sensor hasn't been started yet")
            try:
                tempSocket.sendall(b"{}\n")
            except OSError:
                pass
            self._clientSocket=None
class LocatorOrSensor(LocatorRecorderOrSensor):
    def read(self)->Tuple[int,Dict[str,Any]]:
        with self._readLock:
            if "serial_number" in self._result:
                serialNumber=self._result["serial_number"]
            else:
                serialNumber=-1
            if "data" in self._result:
                result=deepcopy(self._result["data"])
            else:
                result={}
        return serialNumber,result
class Location(LocatorOrSensor):
    @staticmethod
    def requestPermission(remoteContext:Optional[Context]=None)->Optional[str]:
        if remoteContext is None:
            return runString("runtime.requestPermissions([\"access_fine_location\"]);","%s-%d"%(CONFIG["location_permission_title"],time_ns()))
        else:
            remoteContext.call("runtime.requestPermissions([\"access_fine_location\"]);")
    def start(self,locationProvider:str=CONFIG["default_location_provider"],updateDelay:int=CONFIG["default_locating_delay"])->str:
        usedProvider=str(locationProvider)
        for i in usedProvider:
            if i not in CONFIG["location_provider_characters"]:
                raise ValueError("Invalid location provider name")
        usedDelay=int(updateDelay)
        if usedDelay<0 or usedDelay>CONFIG["max_locating_delay"]:
            raise ValueError("The delay out of range")
        with self._mainLock:
            if self._clientSocket is not None:
                raise AttributeError("The locator has already been started")
            with socket() as serverSocket:
                serverPort=bindAvailablePort(serverSocket,1)
                result=runString(LOCATOR_SCRIPT%(CONFIG["script_host_name"],serverPort),"%s-%d"%(CONFIG["locator_title"],time_ns()))
                clientSocket=serverSocket.accept()[0]
            Thread(target=locatorAndSensorMain,args=(self._readLock,self._callbackLock,self._endCallbackLock,self._result,self._callback,self._endCallback,clientSocket,{"delay":usedDelay,"distance":CONFIG["min_locating_distance"],"provider":usedProvider})).start()
            self._clientSocket=clientSocket
        return result
class Recorder(LocatorRecorderOrSensor):
    @staticmethod
    def requestPermission(remoteContext:Optional[Context]=None)->Optional[str]:
        if remoteContext is None:
            return runString("runtime.requestPermissions([\"record_audio\"]);","%s-%d"%(CONFIG["record_permission_title"],time_ns()))
        else:
            remoteContext.call("runtime.requestPermissions([\"record_audio\"]);")
    def start(self,audioSource:str=CONFIG["default_record_source"])->str:
        usedSource=str(audioSource)
        for i in usedSource:
            if i not in CONFIG["record_source_characters"]:
                raise ValueError("Invalid audio source name")
        with self._mainLock:
            if self._clientSocket is not None:
                raise AttributeError("The recorder has already been started")
            with socket() as serverSocket:
                serverPort=bindAvailablePort(serverSocket,1)
                result=runString(RECORDER_SCRIPT%(CONFIG["script_host_name"],serverPort),"%s-%d"%(CONFIG["recorder_title"],time_ns()))
                clientSocket=serverSocket.accept()[0]
            Thread(target=recorderMain,args=(self._readLock,self._callbackLock,self._endCallbackLock,self._result,self._callback,self._endCallback,clientSocket,CONFIG["max_receive_size"],array(CONFIG["audio_array_type"]).itemsize,CONFIG["audio_array_type"],{"bufferratio":CONFIG["record_buffer_ratio"],"channel":CONFIG["record_channel"],"format":CONFIG["record_format"],"samplerate":CONFIG["record_sample_rate"],"source":usedSource})).start()
            self._clientSocket=clientSocket
        return result
    def read(self)->Tuple[int,ArrayType]:
        with self._readLock:
            if "serial_number" in self._result:
                serialNumber=self._result["serial_number"]
            else:
                serialNumber=-1
            if "data" in self._result:
                result=array(CONFIG["audio_array_type"],self._result["data"])
            else:
                result=array(CONFIG["audio_array_type"])
        return serialNumber,result
class Sensor(LocatorOrSensor):
    def start(self,sensorType:str=CONFIG["default_sensor_type"],sensorDelay:int=CONFIG["default_sensor_delay"])->str:
        usedType=str(sensorType)
        for i in usedType:
            if i not in CONFIG["sensor_type_characters"]:
                raise ValueError("Invalid sensor type name")
        usedDelay=int(sensorDelay)
        if usedDelay<0 or usedDelay>CONFIG["max_sensor_delay"]:
            raise ValueError("The delay out of range")
        with self._mainLock:
            if self._clientSocket is not None:
                raise AttributeError("The sensor has already been started")
            with socket() as serverSocket:
                serverPort=bindAvailablePort(serverSocket,1)
                result=runString(SENSOR_SCRIPT%(CONFIG["script_host_name"],serverPort),"%s-%d"%(CONFIG["sensor_title"],time_ns()))
                clientSocket=serverSocket.accept()[0]
            Thread(target=locatorAndSensorMain,args=(self._readLock,self._callbackLock,self._endCallbackLock,self._result,self._callback,self._endCallback,clientSocket,{"delay":usedDelay,"latency":CONFIG["max_sensor_latency"],"type":usedType})).start()
            self._clientSocket=clientSocket
        return result