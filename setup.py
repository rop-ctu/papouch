from setuptools import setup

setup(name='papouch',
      version='0.1',
      description='Library for Papouch devices',
      url='https://gitlab.ciirc.cvut.cz/b635/papouch',
      author='Libor Wagner',
      author_email='libor.wagner@cvut.cz',
      license='CTU',
      packages=['papouch'],
      scripts=['bin/quido-cli', 'bin/quido-test'],
      zip_safe=False)
