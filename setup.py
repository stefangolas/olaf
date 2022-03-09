# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 00:28:02 2022

@author: stefa
"""

from setuptools import setup, find_packages

setup(
    name='olaf',
    version='0.5',
    packages=find_packages(exclude=['tests*', 'examples*']),
    license='MIT',
    description='Open-Source Lab Automation Framework',
    long_description=open('README.md').read(),
    install_requires=['requests', 'pythonnet', 'pywin32', 'pyserial'],
    package_data={'pyhamilton': ['star-oem/*', 'star-oem/VENUS_Method/*']},
    url='https://github.com/dgretton/pyhamilton.git',
    author='Dana Gretton',
    author_email='dgretton@mit.edu'
)
