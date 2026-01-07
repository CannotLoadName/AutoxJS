var clientSocket=new java.net.Socket("localhost",%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var inputObject=new org.json.JSONObject(inputReader.readLine());
var locationManager=context.getSystemService(context.LOCATION_SERVICE);
var outputObject=new org.json.JSONObject();
var outputWriter=new java.io.PrintWriter(clientSocket.getOutputStream(),true);
var stopEmitter=events.emitter(threads.currentThread());
var locationListener=new android.location.LocationListener({
    onLocationChanged:function(location){
        outputObject.put("accuracy",location.getAccuracy());
        outputObject.put("altitude",location.getAltitude());
        outputObject.put("bearing",location.getBearing());
        outputObject.put("bearing_accuracy",location.getBearingAccuracyDegrees());
        outputObject.put("latitude",location.getLatitude());
        outputObject.put("longitude",location.getLongitude());
        outputObject.put("provider",location.getProvider());
        outputObject.put("speed",location.getSpeed());
        outputObject.put("speed_accuracy",location.getSpeedAccuracyMetersPerSecond());
        outputObject.put("time",location.getTime());
        outputObject.put("vertical_accuracy",location.getVerticalAccuracyMeters());
        var outputString=outputObject.toString();
        try{
            outputWriter.println(outputString);
        }
        catch(error){
            stopEmitter.emit("stop");
        }
    }
});
stopEmitter.on("stop",function(){
    locationManager.removeUpdates(locationListener);
    outputWriter.close();
    inputReader.close();
    clientSocket.close();
    stopEmitter.removeAllListeners("stop");
});
locationManager.requestLocationUpdates(eval("locationManager."+inputObject.getString("provider")+"_PROVIDER"),inputObject.getLong("delay"),inputObject.getDouble("distance"),locationListener,android.os.Looper.myLooper());
threads.start(function(){
    try{
        inputReader.readLine();
    }
    finally{
        stopEmitter.emit("stop");
    }
});