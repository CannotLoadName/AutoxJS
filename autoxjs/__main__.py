#-*-coding:utf-8;-*-
if __name__=="__main__":
    from argparse import ArgumentParser
    from importlib import import_module,reload
    from os.path import abspath,dirname,join
    class AutoFilePath(str):
        pass
    class FilePath(str):
        pass
    configFilePath=join(dirname(__spec__.origin),"config.json")
    parser=ArgumentParser(prog="python3 -m %s"%(__spec__.parent,),description="Launch Auto.js and AutoX.js scripts through Python in Termux.",epilog="You can view the config file at \"%s\" to learn about the config items. You can also get more information at \"https://pypi.org/project/AutoxJS/\"."%(abspath(configFilePath),))
    parser.add_argument("-v","--version",action="version",version="AutoxJS 1.0.17")
    parser.add_argument("-a","--autofile",action="append",nargs="+",type=AutoFilePath,help="run Auto.js and AutoX.js auto files",metavar="<file>",dest="script")
    parser.add_argument("-c","--config",action="append",nargs=2,help="modify config values, without changing their data types",metavar=("<key>","<value>"))
    parser.add_argument("-f","--file",action="append",nargs="+",type=FilePath,help="run Auto.js and AutoX.js script files",metavar="<file>",dest="script")
    parser.add_argument("-s","--string",action="append",nargs="+",help="run Auto.js and AutoX.js commands as strings",metavar="<command>",dest="script")
    parser.add_argument("-t","--terminate",action="append",nargs="+",help="force stop Auto.js and AutoX.js scripts based on their names",metavar="<name>")
    parseResult=parser.parse_args()
    if parseResult.config or parseResult.script or parseResult.terminate:
        runner=import_module(".runner",__spec__.parent)
        if parseResult.config:
            from copy import deepcopy
            from json import dump
            configFile=deepcopy(runner.CONFIG)
            for i in parseResult.config:
                configFile[i[0]]=type(configFile[i[0]])(i[1])
                print("Config item \"%s\" has been changed to \"%s\""%(i[0],i[1]))
            dump(configFile,open(configFilePath,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
            if parseResult.script or parseResult.terminate:
                runner=reload(runner)
        if parseResult.script:
            for i in parseResult.script:
                for j in i:
                    if isinstance(j,AutoFilePath):
                        scriptName=runner.runAutoFile(str(j))
                    elif isinstance(j,FilePath):
                        scriptName=runner.runFile(str(j))
                    else:
                        scriptName=runner.runString(j)
                    print("\"%s\" was launched"%(scriptName,))
        if parseResult.terminate:
            sourceNames=[]
            for i in parseResult.terminate:
                for j in i:
                    sourceNames.append(j)
                    print("\"%s\" will be stopped"%(j,))
            runner.forceStop(sourceNames)
    else:
        parser.error("no valid arguments entered")