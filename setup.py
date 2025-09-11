# encoding: utf-8
#
import os
import re
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

def extract_requirements(req_file_path: str) -> list[str]:
    """
    Read requirements file and return list of requirements
    """
    req_lst: list[str] = []

    with open(req_file_path, "rt") as req_file:
        for line in req_file:
            req = re.sub(r"\s+", "", line, flags=re.UNICODE)
            req = req.split("#")[0] # skip comment

            if len(req):  # skip empty line
                req_lst.append(req)
    return req_lst

# Get current version from the VERSION file
with open(os.path.join(here, 'volue_insight_timeseries/VERSION')) as fv:
    version = fv.read().strip()

setup(
    name='volue_insight_timeseries',
    python_requires='>=3.10, <3.14',
    packages=find_packages(),
    install_requires=extract_requirements('requirements.txt'),
    tests_require=[
        'pytest',
        'pytest-cov >= 2.5',
        'requests-mock >= 1.3',
    ],
    version=version,
    description='Volue Insight API python library',
    long_description='This library is meant as a simple toolkit for working with data from https://api.volueinsight.com/ (or equivalent services).  Note that access is based on some sort of login credentials, this library is not all that useful unless you have a valid Volue Insight account.',
    package_data={'volue_insight_timeseries': ['VERSION']},
    author='Volue Insight',
    author_email='support.insight@volue.com',
    url='https://www.volueinsight.com'
)
