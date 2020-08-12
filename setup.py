from brawlpython import __version__
from setuptools import find_packages, setup


with open("README.md", "r") as file:
    long_description = file.read()

with open("requirements.txt", "r") as file:
    requirements = [line.strip() for line in file]

github_link = "https://github.com/0dminnimda/brawlpython"

setup(
    name="brawlpython",
    version=__version__,
    description="Easy-to-configure library to use any Brawl Stars API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="0dminnimda",
    author_email="0dminnimda@gmail.com",
    url=github_link,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 1 - Planning",
        "Framework :: AsyncIO",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Natural Language :: English",
        "Topic :: Games/Entertainment :: Real Time Strategy",
        "Topic :: Internet :: WWW/HTTP :: Session",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    license="MIT",
    keywords=(
        "brawl stars, brawl stars api, brawlstars,"
        "supercell, brawl, stars, api,"
        "brawlpython, python, async, aiohttp, sync, requests,"
    ),
    project_urls={
        # "Documentation": "Coming soon",
        # "Funding": "Haven\'t done yet :(",
        "Say Thanks!": "https://saythanks.io/to/0dminnimda%40gmail.com",
        "Source": github_link,
        "Bug tracker": github_link + "/issues",
    },
    install_requires=requirements,
    python_requires="~=3.8",
)
