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
        "-v", "-r A",
        "--show-capture=stdout",
        cov,
    ])

    # cmd usage:
    # run from the root directory:
    # pytest tests/ -v -r A --show-capture=stdout --cov=brawlpython


if __name__ == "__main__":
    run()
