#-*-coding:utf-8;-*-
from setuptools import setup
setup(
    name="AutoxJS",
    version="1.0.12",
    description="Launch Auto.js and AutoX.js scripts through Python in Termux.",
    long_description="Run \"pip install AutoxJS\" to install this package.<br/>Then run \"python3 -m autojs -h\" to learn how to use this package.<br/>For new versions of AutoX.js, running \"python3 -m autojs -c intent_component org.autojs.autoxjs/.external.open.RunIntentActivity\" to change the package name may be necessary.",
    long_description_content_type="text/markdown",
    author="Enbuging",
    author_email="electricfan@yeah.net",
    url="https://github.com/CannotLoadName/AutoxJS",
    download_url="https://github.com/CannotLoadName/AutoxJS/releases",
    packages=["autojs"],
    license="MIT License",
    keywords=["Auto.js","AutoX.js","Termux","Android","automation"],
    platforms=["Android","Linux"],
    package_data={"autojs":["autorunner.js","filerunner.js","stringrunner.js","locator.js","recorder.js","sensor.js","config.json"]},
    zip_safe=True
)