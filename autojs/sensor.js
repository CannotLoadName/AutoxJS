var clientSocket=new java.net.Socket("localhost",%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var inputObject=new org.json.JSONObject(inputReader.readLine());
var sensorManager=context.getSystemService(context.SENSOR_SERVICE);
var outputObject=new org.json.JSONObject();
var outputWriter=new java.io.PrintWriter(clientSocket.getOutputStream(),true);
var stopEmitter=events.emitter(threads.currentThread());
var sensorListener=new android.hardware.SensorEventListener({
    onSensorChanged:function(event){
        outputObject.put("accuracy",event.accuracy);
        outputObject.put("timestamp",event.timestamp);
        outputObject.put("values",new org.json.JSONArray(event.values));
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
    sensorManager.unregisterListener(sensorListener);
    outputWriter.close();
    inputReader.close();
    clientSocket.close();
    stopEmitter.removeAllListeners("stop");
});
sensorManager.registerListener(sensorListener,sensorManager.getDefaultSensor(eval("android.hardware.Sensor.TYPE_"+inputObject.getString("type"))),inputObject.getInt("delay"),inputObject.getInt("latency"),new android.os.Handler(android.os.Looper.myLooper()));
threads.start(function(){
    try{
        inputReader.readLine();
    }
    finally{
        stopEmitter.emit("stop");
    }
});