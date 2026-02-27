"""Setup script for the onvif_zeep package."""
import os
import sysconfig
import shutil
from setuptools import setup, find_packages
from setuptools.command.install import install


here = os.path.abspath(os.path.dirname(__file__))
version_path = os.path.join(here, 'onvif/version.txt')
version = open(version_path).read().strip()

requires = ['zeep >= 3.0.0']

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Customer Service',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Telecommunications Industry',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Utilities',
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.5",
]


class CustomInstallCommand(install):
    """Custom install command to handle WSDL files."""
    def run(self):
        # Run regular installation first
        install.run(self)

        # Now manually copy the wsdl files to site-packages/wsdl
        wsdl_src_dir = 'wsdl'
        wsdl_dst_dir = os.path.join(sysconfig.get_paths()['purelib'], 'wsdl')

        os.makedirs(wsdl_dst_dir, exist_ok=True)

        for file in os.listdir(wsdl_src_dir):
            src_path = os.path.join(wsdl_src_dir, file)
            dst_path = os.path.join(wsdl_dst_dir, file)
            shutil.copyfile(src_path, dst_path)


setup(
    name='onvif_zeep',
    version=version,
    description='Python Client for ONVIF Camera',
    long_description=open('README.rst', 'r').read(),
    author='Cherish Chen',
    author_email='sinchb128@gmail.com',
    maintainer='sinchb',
    maintainer_email='sinchb128@gmail.com',
    license='MIT',
    keywords=['ONVIF', 'Camera', 'IPC'],
    url='http://github.com/quatanium/python-onvif',
    zip_safe=False,
    packages=find_packages(exclude=['docs', 'examples', 'tests']),
    install_requires=requires,
    entry_points={
        'console_scripts': ['onvif-cli = onvif.cli:main']
    },
    cmdclass={
        'install': CustomInstallCommand,
    },
)
