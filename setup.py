# -*- coding: utf-8 -*-

from brawlpython import __version__, __name__
from setuptools import find_packages, setup


with open("README.md", "r") as file:
    long_description = file.read()

with open("requirements/common.txt", "r") as file:
    requirements = [line.strip() for line in file]

github_link = "https://github.com/0dminnimda/{0}".format(__name__)

setup(
    name=__name__,
    version=__version__,
    description="Easy-to-configure library to use Official and other Brawl Stars API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="0dminnimda",
    author_email="0dminnimda.contact@gmail.com",
    url=github_link,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Games/Entertainment :: Real Time Strategy",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    license="MIT",
    keywords=[
        "brawl stars, brawl stars api, brawlstars,"
        "supercell, brawl, stars, api,"
        "brawlpython, python, async, aiohttp, sync, requests,"
    ],
    project_urls={
        # "Documentation": "Coming soon",
        # "Funding": "Haven\'t done yet :(",
        "Say Thanks!": "https://saythanks.io/to/"\
        "0dminnimda.contact%40gmail.com",
        # "Source": github_link,
        # as long as the `url` parameter does not differ from
        # `project_urls["Source"]`, the latter is meaningless
        "Bug tracker": github_link + "/issues",
        "Code examples": github_link + "/tree/master/examples",
    },
    install_requires=requirements,
    python_requires="~=3.6",
)
