#!/usr/bin/env python

from distutils.core import setup

setup(name='RoutePlotter',
      version='1.0',
      description='Scanning spectrometer flight-route calculator with gui',
      author='Matthew Westphall',
      author_email='w.matthew.he@gmail.com',
      packages=['RoutePlotter'],
      package_data={'': ['**/**/*.js','**/**/*.html','**/**/*.css','**/**/*.png']},
      scripts=['scan_route_plotter'],
      install_requires=[
        'pyshp',
        'cefpython3',
        'lxml',
        'numpy'
      ],
     )
