#-*-coding:utf-8;-*-
from json import dumps,loads
from os.path import dirname,join
from socket import AF_INET,SOCK_STREAM,SocketType,socket
from time import time_ns
from typing import Any,Optional
from .runner import CONFIG,bindAvailablePort,runString
REMOTE_CALLER=open(join(dirname(__spec__.origin),"remotecaller.js"),"r",encoding="utf-8").read()
class Context:
    _clientSocket:Optional[SocketType]
    def __init__(self)->None:
        self._clientSocket=None
    def __enter__(self):
        self.open()
        return self
    def __setitem__(self,key:str,value:Any)->None:
        self.set(key,value)
    def __getitem__(self,key:str)->Any:
        return self.get(key)
    def __exit__(self,exc_type,exc_val,exc_tb):
        self.close()
        return False
    def __del__(self)->None:
        tempSocket=self._clientSocket
        if tempSocket is not None:
            try:
                tempSocket.sendall(b"{}\n")
            except OSError:
                pass
            try:
                tempSocket.close()
            except OSError:
                pass
    def open(self,auto:bool=False)->None:
        if self._clientSocket is not None:
            raise AttributeError("The context has already been opened")
        with socket(AF_INET,SOCK_STREAM) as serverSocket:
            serverPort=bindAvailablePort(serverSocket,1)
            if auto:
                script="\"auto\";\n"+REMOTE_CALLER%(CONFIG["script_host_name"],serverPort)
            else:
                script=REMOTE_CALLER%(CONFIG["script_host_name"],serverPort)
            runString(script,"%s-%d"%(CONFIG["remote_caller_title"],time_ns()))
            self._clientSocket=serverSocket.accept()[0]
    def set(self,key:str,value:Any)->None:
        if self._clientSocket is None:
            raise AttributeError("The context hasn't been opened yet")
        self._clientSocket.sendall((dumps({"key":str(key),"value":value},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
    def call(self,function:str,**kwargs:Any)->Any:
        if self._clientSocket is None:
            raise AttributeError("The context hasn't been opened yet")
        keys=[]
        values=[]
        for i,j in kwargs.items():
            keys.append(str(i))
            values.append(j)
        self._clientSocket.sendall((dumps({"args":values,"keys":keys,"target":str(function)},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
        with self._clientSocket.makefile("r",encoding="utf-8") as socketReader:
            result=loads(socketReader.readline())
        if "result" in result:
            return result["result"]
        elif "error" in result:
            raise ValueError("The JavaScript function threw an error: %s"%(result["error"],))
    def get(self,key:str)->Any:
        if self._clientSocket is None:
            raise AttributeError("The context hasn't been opened yet")
        self._clientSocket.sendall((dumps({"key":str(key)},ensure_ascii=False,separators=(",",":"))+"\n").encode("utf-8"))
        with self._clientSocket.makefile("r",encoding="utf-8") as socketReader:
            result=loads(socketReader.readline())
        if "result" in result:
            return result["result"]
        elif "error" in result:
            raise KeyError("During the query, an error was thrown: %s"%(result["error"],))
    def close(self)->None:
        tempSocket=self._clientSocket
        if tempSocket is None:
            raise AttributeError("The context hasn't been opened yet")
        try:
            tempSocket.sendall(b"{}\n")
        except OSError:
            pass
        try:
            tempSocket.close()
        except OSError:
            pass
        self._clientSocket=None