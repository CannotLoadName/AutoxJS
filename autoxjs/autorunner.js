var clientSocket=new java.net.Socket(%r,%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var inputObject=new org.json.JSONObject(inputReader.readLine());
inputReader.close();
clientSocket.close();
engines.execAutoFile(inputObject.getString("file"),{path:inputObject.getString("path")});