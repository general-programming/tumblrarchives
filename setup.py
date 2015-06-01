import os

from setuptools import setup, find_packages
from pip.req import parse_requirements

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md')) as f:
    README = f.read()

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements(os.path.join(here, "requirements.txt"), session="foobar")

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

CHANGES = ""

setup(
    name="archives",
    packages=find_packages(),
    zip_safe=False,
    install_requires=reqs,
)
