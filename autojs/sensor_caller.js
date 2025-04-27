var client=new java.net.Socket("localhost",%d);
var inputBuffer=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),"utf-8"));
var inputObject=JSON.parse(inputBuffer.readLine());
var outputBuffer=new java.io.PrintWriter(client.getOutputStream());
var sensorManager=context.getSystemService(context.SENSOR_SERVICE);
var stopEvent=events.emitter(threads.currentThread());
var sensorListener=new android.hardware.SensorEventListener({
    onSensorChanged:function(event){
        var outputString=JSON.stringify({
            accuracy:event.accuracy,
            time:event.timestamp,
            values:event.values
        })+"\n";
        try{
            outputBuffer.write(outputString);
            outputBuffer.flush();
        }
        catch(error){
            stopEvent.emit("stop");
        }
    }
});
switch(inputObject.type){
    case "accelerometer":
    var sensorType=android.hardware.Sensor.TYPE_ACCELEROMETER;
    break;
    case "gravity":
    var sensorType=android.hardware.Sensor.TYPE_GRAVITY;
    break;
    case "gyroscope":
    var sensorType=android.hardware.Sensor.TYPE_GYROSCOPE;
    break;
    case "light":
    var sensorType=android.hardware.Sensor.TYPE_LIGHT;
    break;
    case "linear_acceleration":
    var sensorType=android.hardware.Sensor.TYPE_LINEAR_ACCELERATION;
    break;
    case "magnetic_field":
    var sensorType=android.hardware.Sensor.TYPE_MAGNETIC_FIELD;
    break;
    case "orientation":
    var sensorType=android.hardware.Sensor.TYPE_ORIENTATION;
    break;
    case "proximity":
    var sensorType=android.hardware.Sensor.TYPE_PROXIMITY;
    break;
    case "rotation_vector":
    var sensorType=android.hardware.Sensor.TYPE_ROTATION_VECTOR;
    break;
    default:
    var sensorType=android.hardware.Sensor.TYPE_STEP_COUNTER;
}
stopEvent.on("stop",function(){
    sensorManager.unregisterListener(sensorListener);
    outputBuffer.close();
    inputBuffer.close();
    client.close();
    stopEvent.removeAllListeners("stop");
});
sensorManager.registerListener(sensorListener,sensorManager.getDefaultSensor(sensorType),inputObject.delay,new android.os.Handler(android.os.Looper.myLooper()));
threads.start(function(){
    try{
        inputBuffer.readLine();
    }
    finally{
        stopEvent.emit("stop");
    }
});