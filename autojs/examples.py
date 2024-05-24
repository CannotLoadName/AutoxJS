from time import time_ns
from threading import Thread, Lock
from json import dumps, loads
from .core import getServer, runString

locationScript = """var socket=new java.net.Socket("localhost",%d);
var in_byte=socket.getInputStream();
var in_char=new java.io.InputStreamReader(in_byte,"utf-8");
var in_buf=new java.io.BufferedReader(in_char);
var out_byte=socket.getOutputStream();
var out_buf=new java.io.PrintWriter(out_byte);
var in_json=JSON.parse(in_buf.readLine());
var ll=new android.location.LocationListener(){
    onLocationChanged(location){
        out_buf.write(JSON.stringify({
            accuracy:location.getAccuracy(),
            altitude:location.getAltitude(),
            bearing:location.getBearing(),
            bearing_accuracy:location.getBearingAccuracyDegrees(),
            latitude:location.getLatitude(),
            longitude:location.getLongitude(),
            provider:location.getProvider(),
            speed:location.getSpeed(),
            speed_accuracy:location.getSpeedAccuracyMetersPerSecond(),
            time:location.getTime(),
            vertical_accuracy:location.getVerticalAccuracyMeters()
        })+"\\n");
        out_buf.flush();
    }
};
var lm=context.getSystemService(android.content.Context.LOCATION_SERVICE);
if(in_json.provider=="gps"){
    var lp=lm.GPS_PROVIDER;
}
else{
    var lp=lm.NETWORK_PROVIDER;
}
lm.requestLocationUpdates(lp,in_json.delay,0,ll,android.os.Looper.myLooper());
var stop=false;
var interval=timers.setInterval(function(){
    if(stop){
        lm.removeUpdates(ll);
        out_buf.close();
        out_byte.close();
        in_buf.close();
        in_char.close();
        in_byte.close();
        socket.close();
        timers.clearInterval(interval);
    }
},200);
threads.start(function(){
    try{
        in_buf.readLine();
    }
    catch(err){}
    finally{
        stop=true;
    }
});
"""
sensorScript = """var socket=new java.net.Socket("localhost",%d);
var in_byte=socket.getInputStream();
var in_char=new java.io.InputStreamReader(in_byte,"utf-8");
var in_buf=new java.io.BufferedReader(in_char);
var out_byte=socket.getOutputStream();
var out_buf=new java.io.PrintWriter(out_byte);
var in_json=JSON.parse(in_buf.readLine());
var sl=new android.hardware.SensorEventListener(){
    onSensorChanged(event){
        out_buf.write(JSON.stringify({
            accuracy:event.accuracy,
            time:event.timestamp,
            values:event.values
        })+"\\n");
        out_buf.flush();
    }
};
var sm=context.getSystemService(android.content.Context.SENSOR_SERVICE);
switch(in_json.type){
    case "accelerometer":
    var st=android.hardware.Sensor.TYPE_ACCELEROMETER;
    break;
    case "gravity":
    var st=android.hardware.Sensor.TYPE_GRAVITY;
    break;
    case "gyroscope":
    var st=android.hardware.Sensor.TYPE_GYROSCOPE;
    break;
    case "light":
    var st=android.hardware.Sensor.TYPE_LIGHT;
    break;
    case "linear_acceleration":
    var st=android.hardware.Sensor.TYPE_LINEAR_ACCELERATION;
    break;
    case "magnetic_field":
    var st=android.hardware.Sensor.TYPE_MAGNETIC_FIELD;
    break;
    case "orientation":
    var st=android.hardware.Sensor.TYPE_ORIENTATION;
    break;
    case "proximity":
    var st=android.hardware.Sensor.TYPE_PROXIMITY;
    break;
    case "rotation_vector":
    var st=android.hardware.Sensor.TYPE_ROTATION_VECTOR;
    break;
    default:
    var st=android.hardware.Sensor.TYPE_STEP_COUNTER;
}
sm.registerListener(sl,sm.getDefaultSensor(st),in_json.delay*1000,new android.os.Handler(android.os.Looper.myLooper()));
var stop=false;
var interval=timers.setInterval(function(){
    if(stop){
        sm.unregisterListener(sl);
        out_buf.close();
        out_byte.close();
        in_buf.close();
        in_char.close();
        in_byte.close();
        socket.close();
        timers.clearInterval(interval);
    }
},200);
threads.start(function(){
    try{
        in_buf.readLine();
    }
    catch(err){}
    finally{
        stop=true;
    }
});
"""
LOCATION_PROVIDERS = ("gps", "network")
SENSOR_TYPES = (
    "accelerometer", "gravity", "gyroscope", "light", "linear_acceleration", "magnetic_field", "orientation",
    "proximity",
    "rotation_vector", "step_counter")


def copyList(iList):
    ret = []
    for i in iList:
        if type(i) == list:
            ret.append(copyList(i))
        elif type(i) == dict:
            ret.append(copyDict(i))
        else:
            ret.append(i)
    return ret


def copyDict(iDict):
    ret = {}
    for i in iDict:
        if type(iDict[i]) == dict:
            ret[i] = copyDict(iDict[i])
        elif type(iDict[i]) == list:
            ret[i] = copyList(iDict[i])
        else:
            ret[i] = iDict[i]
    return ret


def threadMain(lockRead, lockUpdate, lockEnd, updateCallback, endCallback, result, iSocket, param):
    iStream = iSocket.makefile("r")
    iSocket.send((dumps(param) + "\n").encode("utf-8"))
    while True:
        fLine = iStream.readline()
        if len(fLine) > 0 and fLine[-1] == "\n":
            dct = loads(fLine)
            lockUpdate.acquire()
            for i in updateCallback:
                Thread(target=i, args=(copyDict(dct),)).start()
            lockUpdate.release()
            lockRead.acquire()
            for i in dct:
                result[i] = dct[i]
            lockRead.release()
        else:
            break
    lockEnd.acquire()
    for i in endCallback:
        Thread(target=i).start()
    lockEnd.release()
    lockRead.acquire()
    result.clear()
    lockRead.release()
    iStream.close()
    iSocket.close()


class PrivateAbstract:
    _lockMain = None
    _lockRead = None
    _lockUpdateCallback = None
    _lockEndCallback = None
    _updateCallback = None
    _endCallback = None
    _result = None
    _socket = None

    def __init__(self):
        self._lockMain = Lock()
        self._lockRead = Lock()
        self._lockUpdateCallback = Lock()
        self._lockEndCallback = Lock()
        self._updateCallback = []
        self._endCallback = []
        self._result = {}

    def __del__(self):
        self._lockMain.acquire()
        if self._socket is None:
            self._lockMain.release()
        else:
            try:
                self._socket.send(b"{}\n")
            except Exception:
                pass
            self._lockMain.release()

    def updateCallback(self, iCallback):
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockUpdateCallback.acquire()
        self._updateCallback.append(iCallback)
        self._lockUpdateCallback.release()

    def removeUpdateCallbacks(self):
        self._lockUpdateCallback.acquire()
        self._updateCallback.clear()
        self._lockUpdateCallback.release()

    def endCallback(self, iCallback):
        if not callable(iCallback):
            raise TypeError("The callback function must be a callable object.")
        self._lockEndCallback.acquire()
        self._endCallback.append(iCallback)
        self._lockEndCallback.release()

    def removeEndCallbacks(self):
        self._lockEndCallback.acquire()
        self._endCallback.clear()
        self._lockEndCallback.release()

    def read(self):
        self._lockRead.acquire()
        ret = copyDict(self._result)
        self._lockRead.release()
        return ret

    def stop(self):
        self._lockMain.acquire()
        if self._socket is None:
            self._lockMain.release()
            raise AttributeError("The locator or sensor has already been stopped.")
        try:
            self._socket.send(b"{}\n")
        except Exception:
            pass
        self._socket = None
        self._lockMain.release()


class Location(PrivateAbstract):
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
        if self._socket is not None:
            self._lockMain.release()
            raise AttributeError("The locator has already been started.")
        fServer, fPort = getServer()
        if runString(locationScript % (fPort,), "LocationManager-%d" % (time_ns(),)):
            self._socket, addr = fServer.accept()
            Thread(target=threadMain, args=(
                self._lockRead, self._lockUpdateCallback, self._lockEndCallback, self._updateCallback,
                self._endCallback,
                self._result, self._socket, {"provider": iProvider, "delay": iDelay})).start()
            self._lockMain.release()
            fServer.close()
        else:
            self._lockMain.release()
            fServer.close()
            raise OSError("Unable to launch Auto.js or Autox.js application.")


class Sensor(PrivateAbstract):
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
        if self._socket is not None:
            self._lockMain.release()
            raise AttributeError("The sensor has already been started.")
        fServer, fPort = getServer()
        if runString(sensorScript % (fPort,), "SensorManager-%d" % (time_ns(),)):
            self._socket, addr = fServer.accept()
            Thread(target=threadMain, args=(
                self._lockRead, self._lockUpdateCallback, self._lockEndCallback, self._updateCallback,
                self._endCallback,
                self._result, self._socket, {"type": iType, "delay": iDelay})).start()
            self._lockMain.release()
            fServer.close()
        else:
            self._lockMain.release()
            fServer.close()
            raise OSError("Unable to launch Auto.js or Autox.js application.")
