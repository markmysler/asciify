from setuptools import setup

setup(
    name='asciifyy',
    version='1.0.0',
    py_modules=['asciify'],
    install_requires=['pillow', 'colorama'],
    entry_points={
        'console_scripts': [
            'asciify=asciify:main',
        ],
    },
)
