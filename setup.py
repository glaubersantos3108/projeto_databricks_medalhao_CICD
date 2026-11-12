"""
setup.py configuration script describing how to build and package this project.

This file is primarily used by the setuptools library and typically should not
be executed directly. See README.md for how to deploy, test, and run
the projeto_databricks_medalhao_CICD project.
"""

from setuptools import setup, find_packages

import sys

sys.path.append("./src")

import datetime
import projeto_databricks_medalhao_CICD

local_version = datetime.datetime.utcnow().strftime("%Y%m%d.%H%M%S")

setup(
    name="projeto_databricks_medalhao_CICD",
    # We use timestamp as Local version identifier (https://peps.python.org/pep-0440/#local-version-identifiers.)
    # to ensure that changes to wheel package are picked up when used on all-purpose clusters
    version=projeto_databricks_medalhao_CICD.__version__ + "+" + local_version,
    url="https://databricks.com",
    author="glauber.santos90@outlook.com",
    description="wheel file based on projeto_databricks_medalhao_CICD/src",
    packages=find_packages(where="./src"),
    package_dir={"": "src"},
    entry_points={
        "packages": [
            "main=projeto_databricks_medalhao_CICD.main:main",
        ],
    },
    install_requires=[
        # Dependencies in case the output wheel file is used as a library dependency.
        # For defining dependencies, when this package is used in Databricks, see:
        # https://docs.databricks.com/dev-tools/bundles/library-dependencies.html
        "setuptools"
    ],
)