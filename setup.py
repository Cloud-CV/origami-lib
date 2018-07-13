#!/usr/bin/env python

from setuptools import setup, find_packages

PROJECT = "origami_lib"

with open('README.md') as readme_file:
    README = readme_file.read()

install_requires = [
  'flask==1.0.2 ',
  'Flask-Cors==3.0.4',
  'requests==2.18.4',
  'python-magic==0.4.15',
  'tornado==5.0.2',
  'numpy==1.14.3',
  'opencv-python==3.4.1.15',
]

setup(
  name=PROJECT,
  version='0.1',

  description='Library to set up your project to run on Origami',
  long_description=README,

  author='CloudCV Team',
  author_email='team@cloudcv.org',
  url='https://github.com/Cloud-CV/origami-lib',
  packages=find_packages(exclude=['tests']),
  include_package_data=True,

  download_url='https://github.com/Cloud-CV/origami-lib',

  install_requires=install_requires,
  classifiers=[
    'Development Status :: 1 - Alpha',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Intended Audience :: Developers',
    'Environment :: Console',
  ],

  zip_safe=False
)
