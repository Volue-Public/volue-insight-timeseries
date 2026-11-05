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
    # Supported Python versions policy:
    # https://docs.volue.com/data-and-forecasts/volue-insight-timeseries/getting-started/installation#supported-python-versions
    # No upper cap: a cap makes pip on a newer Python fall back to an old release.
    # Raising the minimum drops users on that version, so it needs a major release.
    python_requires='>=3.9',
    packages=find_packages(),
    install_requires=extract_requirements('requirements.txt'),
    extras_require={
        'pandas': ['pandas>=1.5.0'],
    },
    tests_require=[
        'pytest',
        'pytest-cov >= 2.5',
        'requests-mock >= 1.3',
    ],
    version=version,
    description='Volue Data & Forecasts API python library',
    long_description=(
        'Python library for the Volue Data & Forecasts Timeseries API. '
        'You need a Volue Data & Forecasts account. '
        'Documentation: https://docs.volue.com/data-and-forecasts/volue-insight-timeseries/'
    ),
    package_data={'volue_insight_timeseries': ['VERSION']},
    author='Volue Data & Forecasts',
    license='MIT',
    author_email='df.support@volue.com',
    url='https://www.volue.com/data-and-forecasts',
    # Tested Python versions: keep in line with .github/workflows/unittests.yml
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
)
