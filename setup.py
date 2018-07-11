# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

setup(
    name="glow",
    version=open("version").read(),
    packages=find_packages(),
    author="Nicolas RAMY",
    author_email="nicolas.ramy@darkelda.com",
    license="MIT",
    description="A new git extension to use git flow branching model automatically on Github",
    long_description=open("README.md").read(),
    data_files=[(".", ["version"])],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "git-glow=glow.__main__:main"
        ],
    },
    install_requires=[
        "colorama",
        "python-slugify",
        "requests",
        "sarge",
        "termcolor",
        "urllib3[secure]"
    ],
    url="https://github.com/nicolasramy/git-glow",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Terminals",
        "Topic :: Utilities"
    ],
)
