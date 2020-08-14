# -*- coding: utf-8 -*-

import pytest


def run(file_name=""):
    file_name = file_name.split("\\")[-1]

    pytest.main([
        "tests/" + file_name,
        "-v", "-r A",
        "--show-capture=stdout",
        "--cov=brawlpython"
    ])

    # cmd usage:
    # if run from the root directory:
    # pytest tests/ -v -r A --show-capture=stdout --cov=brawlpython

    # if run from file directory:
    # pytest ./ -v -r A --show-capture=stdout --cov=brawlpython


if __name__ == "__main__":
    run()
