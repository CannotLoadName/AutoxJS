# -*-coding:utf-8;-*-
from setuptools import setup

setup(
    name="AutoxJS",
    version="1.0.8",
    description="Launch Auto.js and Autox.js scripts with Python in Termux.",
    author="Enbuging",
    author_email="electricfan@yeah.net",
    url="https://github.com/CannotLoadName/AutoxJS",
    download_url="https://github.com/CannotLoadName/AutoxJS/releases",
    packages=["autojs"],
    license="MIT",
    keywords=["Auto.js", "Autox.js", "Termux", "Android", "automation"],
    platforms=["Android", "Linux"],
    package_data={
        "autojs": ["file_runner.js", "string_runner.js", "locator_caller.js", "recorder_caller.js", "sensor_caller.js"]
    },
    zip_safe=True
)
