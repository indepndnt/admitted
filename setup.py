from setuptools import setup

setup(
    name="webfetch",
    version="2022.0",
    description="Utility to make automating processes using Selenium and Chromedriver easier",
    long_description=open("README.md").read(),
    maintainer="Joe Carey",
    maintainer_email="joe@accountingdatasolutions.com",
    url="https://github.com/Accounting-Data-Solutions/webfetch",
    packages=["webfetch"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license=open("LICENSE").read(),
    package_dir={"": "src"},
)
