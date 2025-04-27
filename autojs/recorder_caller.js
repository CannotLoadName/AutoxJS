var client=new java.net.Socket("localhost",%d);
var inputBuffer=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),"utf-8"));
var inputObject=JSON.parse(inputBuffer.readLine());
var outputBuffer=client.getOutputStream();
if(inputObject.channel=="mono"){
    var audioChannel=android.media.AudioFormat.CHANNEL_IN_MONO;
}
else{
    var audioChannel=android.media.AudioFormat.CHANNEL_IN_STEREO;
}
if(inputObject.format=="8bit"){
    var audioFormat=android.media.AudioFormat.ENCODING_PCM_8BIT;
}
else{
    var audioFormat=android.media.AudioFormat.ENCODING_PCM_16BIT;
}
var bufferSize=android.media.AudioRecord.getMinBufferSize(inputObject.samplerate,audioChannel,audioFormat);
var audioRecorder=new android.media.AudioRecord(android.media.MediaRecorder.AudioSource.MIC,inputObject.samplerate,audioChannel,audioFormat,bufferSize);
var stopEvent=events.emitter(threads.currentThread());
var outputBytes=java.lang.reflect.Array.newInstance(java.lang.Byte.TYPE,bufferSize);
var recorderListener=new android.media.AudioRecord.OnRecordPositionUpdateListener({
    onPeriodicNotification:function(recorder){
        var outputLength=recorder.read(outputBytes,0,bufferSize,recorder.READ_NON_BLOCKING);
        if(outputLength>0){
            try{
                outputBuffer.write(outputBytes,0,outputLength);
                outputBuffer.flush();
            }
            catch(error){
                stopEvent.emit("stop");
            }
        }
    }
});
audioRecorder.setPositionNotificationPeriod(Math.floor(audioRecorder.getBufferSizeInFrames()/2));
audioRecorder.setRecordPositionUpdateListener(recorderListener,new android.os.Handler(android.os.Looper.myLooper()));
stopEvent.on("stop",function(){
    audioRecorder.stop();
    audioRecorder.release();
    outputBuffer.close();
    inputBuffer.close();
    client.close();
    stopEvent.removeAllListeners("stop");
});
audioRecorder.startRecording();
threads.start(function(){
    try{
        inputBuffer.readLine();
    }
    finally{
        stopEvent.emit("stop");
    }
});