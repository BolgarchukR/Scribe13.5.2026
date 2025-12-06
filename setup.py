from setuptools import setup, find_packages

# Read the contents of your requirements file
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='scribe-voice',
    version='0.1.0',
    author='Scribe Voice App',
    description='A voice-to-text application.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'gui_scripts': [
            'scribe = run:main',
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)