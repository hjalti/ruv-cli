try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.rst') as f:
    readme = f.read()

setup(
    name='ruv',
    version='0.0.9',
    description='Command line interface for RUV',
    long_description=readme,
    url='https://github.com/hjalti/ruv-cli',
    author='Hjalti Magnússon',
    author_email='hjaltmann@gmail.com',
    license='MIT',
    packages=['ruv'],
    install_requires=[
        "beautifulsoup4==4.6.0",
        "requests==2.14.1",
    ],
    entry_points={
        'console_scripts': [
            'ruv=ruv:main',
            'ruv-live=ruv:default_live',
            'ruv2-live=ruv:default_live2',
        ],
    },
)
