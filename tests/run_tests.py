# -*- coding: utf-8 -*-

import pytest


def run(file_name=""):
    file_name = file_name.split("\\")[-1]

    # show cov only when testing all files
    cov = "--cov=brawlpython"
    if file_name != "":
        cov = ""

    pytest.main([
        "tests/" + file_name,
        "-v", "-r fEx",
        "--show-capture=stdout",
        cov,
        "--pycodestyle",
    ])

    # cmd usage:
    # run from the root directory:
    """pytest tests/ -v -r fEx --show-capture=stdout
     --cov=brawlpython --pycodestyle"""


if __name__ == "__main__":
    run()
