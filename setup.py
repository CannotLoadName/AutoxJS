# -*-coding:utf-8;-*-
from setuptools import setup

setup(
    name="AutoxJS",
    version="1.0.7",
    author="Enbuging",
    author_email="electricfan@yeah.net",
    license="MIT",
    description="Launch Auto.js and Autox.js scripts with Python in Termux.",
    keywords=["Auto.js", "Autox.js", "Termux", "Android", "automation"],
    package_data={
        "autojs": ["file_runner.js", "string_runner.js", "locator_caller.js", "recorder_caller.js", "sensor_caller.js"]
    },
    packages=["autojs"]
)
