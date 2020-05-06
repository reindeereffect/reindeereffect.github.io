#! /usr/bin/env python3
# [[file:~/dev/re/2020/05/05/index.org::setup.py][setup.py]]
import os
from setuptools import setup, find_packages

def ls(base):
    return [os.path.join(base, fn) for fn in os.listdir(base)]

setup(name='sudoku',
      version='0.1',
      description='Sudoku',
      packages=find_packages(),
      scripts=ls('bin'),
      zip_safe=False)
# setup.py ends here
