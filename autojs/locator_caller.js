var client=new java.net.Socket("localhost",%d);
var inputBuffer=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),"utf-8"));
var outputBuffer=new java.io.PrintWriter(client.getOutputStream());
var inputObject=JSON.parse(inputBuffer.readLine());
var stopEvent=events.emitter(threads.currentThread());
var locationManager=context.getSystemService(android.content.Context.LOCATION_SERVICE);
if(inputObject.provider=="gps"){
    var locationProvider=locationManager.GPS_PROVIDER;
}
else{
    var locationProvider=locationManager.NETWORK_PROVIDER;
}
var locationListener=new android.location.LocationListener(){
    onLocationChanged(location){
        var outputString=JSON.stringify({
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
        })+"\n";
        try{
            outputBuffer.write(outputString);
            outputBuffer.flush();
        }
        catch(error){
            stopEvent.emit("stop");
        }
    }
};
locationManager.requestLocationUpdates(locationProvider,inputObject.delay,inputObject.distance,locationListener,android.os.Looper.myLooper());
stopEvent.on("stop",function(){
    locationManager.removeUpdates(locationListener);
    outputBuffer.close();
    inputBuffer.close();
    client.close();
    stopEvent.removeAllListeners("stop");
});
threads.start(function(){
    try{
        inputBuffer.readLine();
    }
    catch(error){}
    finally{
        stopEvent.emit("stop");
    }
});