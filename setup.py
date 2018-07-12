from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='ruv',
    version='0.1.0',
    description='Command line interface for RUV (http://www.ruv.is)',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/hjalti/ruv-cli',
    author='Hjalti Magnússon',
    author_email='hjaltmann@gmail.com',
    license='MIT',
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
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ]
)
