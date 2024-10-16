var client=new java.net.Socket("localhost",%d);
var inputBuffer=new java.io.BufferedReader(new java.io.InputStreamReader(client.getInputStream(),"utf-8"));
var inputObject=JSON.parse(inputBuffer.readLine());
inputBuffer.close();
client.close();
engines.execScriptFile(inputObject.file,{path:inputObject.path});