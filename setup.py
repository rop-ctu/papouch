import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='papouch',
      version='0.1',
      description='Library for Papouch devices',
      long_description=read('README.md'),
      url='https://gitlab.ciirc.cvut.cz/b635/papouch',
      author='Libor Wagner',
      author_email='libor.wagner@cvut.cz',
      keywords='papouch spinel io driver',
      license='CTU',
      packages=['papouch'],
      scripts=['bin/quido-cli', 'bin/quido-test'],
      install_requires=[
          'pyserial',
          'requests',
          'docopt'
      ],
      zip_safe=False)
