var clientSocket=new java.net.Socket("localhost",%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var inputObject=new org.json.JSONObject(inputReader.readLine());
var sampleRate=inputObject.getInt("samplerate");
var audioChannel=eval("android.media.AudioFormat.CHANNEL_"+inputObject.getString("channel"));
var audioFormat=eval("android.media.AudioFormat.ENCODING_"+inputObject.getString("format"));
var bufferSize=android.media.AudioRecord.getMinBufferSize(sampleRate,audioChannel,audioFormat);
var audioRecorder=new android.media.AudioRecord(eval("android.media.MediaRecorder.AudioSource."+inputObject.getString("source")),sampleRate,audioChannel,audioFormat,bufferSize);
audioRecorder.setPositionNotificationPeriod(Math.floor(0.5*audioRecorder.getBufferSizeInFrames()));
var outputBytes=java.lang.reflect.Array.newInstance(java.lang.Byte.TYPE,bufferSize);
var outputStream=clientSocket.getOutputStream();
var stopEmitter=events.emitter(threads.currentThread());
var recorderListener=new android.media.AudioRecord.OnRecordPositionUpdateListener({
    onPeriodicNotification:function(recorder){
        var outputLength=recorder.read(outputBytes,0,bufferSize,recorder.READ_NON_BLOCKING);
        if(outputLength>0){
            try{
                outputStream.write(outputBytes,0,outputLength);
                outputStream.flush();
            }
            catch(error){
                stopEmitter.emit("stop");
            }
        }
    }
});
audioRecorder.setRecordPositionUpdateListener(recorderListener,new android.os.Handler(android.os.Looper.myLooper()));
stopEmitter.on("stop",function(){
    audioRecorder.stop();
    audioRecorder.release();
    outputStream.close();
    inputReader.close();
    clientSocket.close();
    stopEmitter.removeAllListeners("stop");
});
audioRecorder.startRecording();
threads.start(function(){
    try{
        inputReader.readLine();
    }
    finally{
        stopEmitter.emit("stop");
    }
});