var clientSocket=new java.net.Socket("%s",%d);
var inputReader=new java.io.BufferedReader(new java.io.InputStreamReader(clientSocket.getInputStream(),"utf-8"));
var namespace=[];
var outputWriter=new java.io.PrintWriter(clientSocket.getOutputStream(),true);
var inputLine,inputObject,key,target,value,success,result,outputObject,outputLine;
while(true){
    try{
        inputLine=inputReader.readLine();
    }
    catch(error){
        break;
    }
    if(inputLine){
        try{
            inputObject=JSON.parse(inputLine);
        }
        catch(error){
            break;
        }
        if("target" in inputObject){
            key=inputObject.keys;
            target=inputObject.target;
            value=inputObject.args;
            success=true;
            try{
                result=new Function(key,target).apply(namespace,value);
            }
            catch(error){
                outputLine=JSON.stringify({error:String(error)});
                success=false;
            }
            finally{
                if(success){
                    outputObject={result:result};
                    try{
                        outputLine=JSON.stringify(outputObject);
                    }
                    catch(error){
                        outputLine=JSON.stringify({error:String(error)});
                    }
                }
                try{
                    outputWriter.println(outputLine);
                }
                catch(error){
                    break;
                }
            }
        }
        else if("value" in inputObject){
            namespace[inputObject.key]=inputObject.value;
        }
        else if("key" in inputObject){
            outputObject={result:namespace[inputObject.key]};
            try{
                outputLine=JSON.stringify(outputObject);
            }
            catch(error){
                outputLine=JSON.stringify({error:String(error)});
            }
            finally{
                try{
                    outputWriter.println(outputLine);
                }
                catch(error){
                    break;
                }
            }
        }
        else{
            break;
        }
    }
    else{
        break;
    }
}
outputWriter.close();
inputReader.close();
clientSocket.close();