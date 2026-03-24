#-*-coding:utf-8;-*-
from typing import Iterable
def compressScript(originScript:Iterable[str])->str:
    result=[]
    for i in originScript:
        lineString=str(i)
        lineStringLength=len(lineString)
        lineList=[]
        leftNotSpace=False
        for j in range(lineStringLength):
            if leftNotSpace or not lineString[j].isspace():
                for k in range(j,lineStringLength):
                    if not lineString[k].isspace():
                        lineList.append(lineString[j])
                        leftNotSpace=True
                        break
                else:
                    break
        result.extend(lineList)
    return "".join(result)