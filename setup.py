from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup_info = dict(name='warlock',
                  version='1.0.0',
                  author='Mustafa Bayramov',
                  author_email="spyroot@gmail.com",
                  url="https://github.com/spyroot/warlock",
                  description='Standalone command line tool to '
                              'optimize caas and iaas layer.',
                  long_description=long_description,
                  long_description_content_type='text/markdown',
                  packages=['warlock'] + ['warlock.' + pkg for pkg in find_packages('warlock')],
                  license="MIT",
                  python_requires='>=3.10',
                  install_requires=requirements,
                  extras_require={
                      "dev": [
                          "pytest >= 3.7"
                      ]
                  },
                  )
setup(**setup_info)