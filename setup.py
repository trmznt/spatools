import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()

requires = [
    'numpy',
    'scipy',
    'matplotlib',
    'pyyaml',
    'pandas',
    'attrs',
    'transaction',
    'sortedcontainers',
    'sqlalchemy',
    ]

setup(name='spatools',
      version='0.1',
      description='spatools',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Programming Language :: Python", ],
      author='Hidayat Trimarsanto',
      author_email='anto@eijkman.go.id',
      url='',
      keywords='snp processing',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      test_suite="spatools",
      entry_points="""\
      [console_scripts]
      spatools = spatools.scripts.run:main
      """, )
