var clientSocket=new java.net.Socket(%r,%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var inputArray=new org.json.JSONObject(inputReader.readLine()).getJSONArray("sources");
inputReader.close();
clientSocket.close();
var selfName=String(engines.myEngine().getSource());
for(var i of engines.all()){
    var sourceName=String(i.getSource());
    if(sourceName!=selfName){
        for(var j=0;j<inputArray.length();j++){
            if(sourceName==inputArray.getString(j)){
                i.forceStop();
                break;
            }
        }
    }
}