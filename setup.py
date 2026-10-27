# encoding: utf-8
#
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

def extract_requirements(req_file_path: str) -> list[str]:
    """
    Read requirements file and return list of requirements
    """
    req_lst: list[str] = []

    with open(req_file_path, "rt") as req_file:
        for line in req_file:
            req = line.strip()
            req = req.split("#")[0].strip()

            if len(req):  # skip empty line
                req_lst.append(req)
    return req_lst

# Get current version from the VERSION file
with open(os.path.join(here, 'volue_insight_timeseries/VERSION')) as fv:
    version = fv.read().strip()

setup(
    name='volue_insight_timeseries',
    python_requires='>=3.11, <3.15',
    packages=find_packages(),
    install_requires=extract_requirements('requirements.txt'),
    extras_require={
        'pandas': [
            'pandas>=1.5.0; python_version == "3.11"',
            'pandas>=2.1.1; python_version == "3.12"',
            'pandas>=2.2.3; python_version == "3.13"',
            'pandas>=2.3.3; python_version == "3.14"',
        ],
    },
    tests_require=[
        'pytest',
        'pytest-cov >= 2.5',
        'requests-mock >= 1.3',
    ],
    version=version,
    description='Volue Data & Forecasts API python library',
    long_description='This library is meant as a simple toolkit for working with data from https://data-forecasts.volue.com/ (or equivalent services).  Note that access is based on some sort of login credentials, this library is not all that useful unless you have a valid Volue Data & Forecasts account.',
    package_data={'volue_insight_timeseries': ['VERSION']},
    author='Volue Data & Forecasts',
    author_email='df.support@volue.com',
    url='https://www.volue.com/data-and-forecasts'
)
