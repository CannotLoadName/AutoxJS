from sys import argv
from .core import runFile

if __name__ == "__main__":
    for i in argv[1:]:
        runFile(i)
