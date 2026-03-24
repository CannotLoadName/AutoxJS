#-*-coding:utf-8;-*-
from setuptools import setup
setup(
    name="AutoxJS",
    version="1.0.17",
    description="Launch Auto.js and AutoX.js scripts through Python in Termux.",
    long_description="""Run `python3 -m autoxjs -h` to learn how to use this package in the console.

The default config is for ozobi's modified AutoX.js version. For Auto.js and old versions of AutoX.js, running `python3 -m autoxjs -c intent_component org.autojs.autojs/.external.open.RunIntentActivity` to change the package name may be necessary.

In other environments such as QPython 3, Pydroid 3 and AidLux, changing config items **am_command**, **am_subcommand**, **am_user** and **temporary_path** may be necessary.

In new versions of Termux, config items above can also be modified to use **termux-am-socket** instead of the slow **termux-am**.

Use `import autoxjs` or `from autoxjs import *` to import this library in your script.

The `autoxjs.runString` function is used to simply run a JavaScript in a string.

The `autoxjs.runFile` function is used to run JavaScript files.

The `autoxjs.runAutoFile` function is used to run Auto.js and AutoX.js recording files.

The `autoxjs.Context` class is used to call JavaScript codes like RPC.

The `autoxjs.requestAutomation` function can request the automation service.

The `autoxjs.forceStop` function can force stop running scripts.

The `autoxjs.Location`, `autoxjs.Recorder` and `autoxjs.Sensor` classes were written as routines, but can also be used as a module. Thus they can be used to access the hardware in the device.

The `autoxjs.compressScript` function can be used to compress long JavaScript codes, making RPC calling faster.

The `autoxjs.bindAvailablePort` function can be used to bind a socket server to a port within the customized range.

The `autojs.injector.startServer` and `autojs.injector.stopServer` functions are used to manage the RPC server of the **autojs** library, in order to allow users not to have to start it manually. This library doesn't depend on it, so if you don't use it, just ignore it.
""",
    long_description_content_type="text/markdown",
    author="Enbuging",
    author_email="electricfan@yeah.net",
    url="https://github.com/CannotLoadName/AutoxJS",
    download_url="https://github.com/CannotLoadName/AutoxJS/releases",
    packages=["autojs","autoxjs"],
    license="MIT License",
    license_files=["LICENSE"],
    keywords=["Auto.js","AutoX.js","Termux","Android","automation"],
    platforms=["Android","Linux"],
    package_data={"autoxjs":["autorunner.js","filerunner.js","stringrunner.js","forcestop.js","remotecaller.js","locator.js","recorder.js","sensor.js","config.json"]},
    zip_safe=True
)