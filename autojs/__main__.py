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
    parser=ArgumentParser(prog="python3 -m %s"%(__spec__.parent,),description="Launch Auto.js and AutoX.js scripts through Python in Termux.",epilog="You can view the config file at the following path to learn about the config items:\n%s"%(abspath(configFilePath),))
    parser.add_argument("-v","--version",action="version",version="AutoxJS 1.0.14")
    parser.add_argument("-a","--auto",action="append",nargs="+",type=AutoFilePath,help="run Auto.js and AutoX.js auto files",metavar="<file>",dest="script")
    parser.add_argument("-c","--config",action="append",nargs=2,help="modify config values, without changing their data types",metavar=("<key>","<value>"))
    parser.add_argument("-f","--file",action="append",nargs="+",type=FilePath,help="run Auto.js and AutoX.js script files",metavar="<file>",dest="script")
    parser.add_argument("-s","--string",action="append",nargs="+",help="run Auto.js and AutoX.js commands as strings",metavar="<command>",dest="script")
    parseResult=parser.parse_args()
    if parseResult.config:
        from copy import deepcopy
        from json import dump
        runner=import_module(".runner",__spec__.parent)
        configFile=deepcopy(runner.CONFIG)
        for i in parseResult.config:
            configFile[i[0]]=type(configFile[i[0]])(i[1])
            print("Config item \"%s\" has been changed to \"%s\""%(i[0],i[1]))
        dump(configFile,open(configFilePath,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        if parseResult.script:
            runner=reload(runner)
            for i in parseResult.script:
                for j in i:
                    if isinstance(j,AutoFilePath):
                        runner.runAutoFile(str(j))
                    elif isinstance(j,FilePath):
                        runner.runFile(str(j))
                    else:
                        runner.runString(j)
    elif parseResult.script:
        runner=import_module(".runner",__spec__.parent)
        for i in parseResult.script:
            for j in i:
                if isinstance(j,AutoFilePath):
                    runner.runAutoFile(str(j))
                elif isinstance(j,FilePath):
                    runner.runFile(str(j))
                else:
                    runner.runString(j)
    else:
        parser.error("no valid arguments entered")