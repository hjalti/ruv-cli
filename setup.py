import os

from setuptools import setup

ROOT = os.path.abspath(os.path.dirname(__file__))

with open('README.md') as f:
    readme = f.read()

about = {}
with open(os.path.join(ROOT, 'ruv', '__version__.py')) as f:
    exec(f.read(), about)

setup(
    name=about['__name__'],
    version=about['__version__'],
    description='Command line interface for RUV (http://www.ruv.is)',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/hjalti/ruv-cli',
    author=about['__author__'],
    author_email=about['__author_email__'],
    license=about['__version__'],
    packages=['ruv'],
    python_requires='>=3.6.0',
    install_requires=[
        "requests",
    ],
    entry_points={
        'console_scripts': [
            'ruv=ruv:main',
            'ruv-live=ruv:default_live',
            'ruv2-live=ruv:default_live2',
        ],
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
