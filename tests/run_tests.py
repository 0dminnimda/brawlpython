# -*- coding: utf-8 -*-

import pytest


def run(file_name=""):
    file_name = file_name.split("\\")[-1]

    # show cov only when testing all files
    add = [
        "--cov=brawlpython",
    ]

    if file_name != "":
        add = []

    pytest.main([
        "tests/" + file_name,
        "-v", "-r fExP",
        "--show-capture=stdout",
        "--pycodestyle",
    ] + add)

    # cmd usage:
    # run from the root directory:
    """pytest tests/ -v -r fExP --show-capture=stdout
     --cov=brawlpython --pycodestyle"""


if __name__ == "__main__":
    run()
