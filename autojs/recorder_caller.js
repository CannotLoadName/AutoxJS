var client=new java.net.Socket("localhost",%d);
var inputBuffer=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),"utf-8"));
var outputBuffer=client.getOutputStream();
var inputObject=JSON.parse(inputBuffer.readLine());
var stopEvent=events.emitter(threads.currentThread());
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
var outputBytes=java.lang.reflect.Array.newInstance(java.lang.Byte.TYPE,bufferSize);
var recorderListener=new android.media.AudioRecord.OnRecordPositionUpdateListener(){
    onPeriodicNotification(recorder){
        var outputLength=recorder.read(outputBytes,0,bufferSize,android.media.AudioRecord.READ_NON_BLOCKING);
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
};
audioRecorder.setPositionNotificationPeriod(Math.floor(audioRecorder.getBufferSizeInFrames()/2));
audioRecorder.setRecordPositionUpdateListener(recorderListener,new android.os.Handler(android.os.Looper.myLooper()));
audioRecorder.startRecording();
stopEvent.on("stop",function(){
    audioRecorder.stop();
    audioRecorder.release();
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