#! /usr/bin/env python3
import os
from setuptools import setup, find_packages

def ls(base):
    return [os.path.join(base, fn) for fn in os.listdir(base)]

setup(name='sudoku',
      version='0.1',
      description='Sudoku',
      packages=find_packages(),
      scripts=ls('bin'),
      include_package_data=True,
      zip_safe=False)
