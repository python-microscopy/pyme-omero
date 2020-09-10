#!/usr/bin/env python

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

def install_pyme_plugin():
    import sys
    import subprocess
    import os
    plugin_install_path = os.path.join(os.path.dirname(__file__), 
                                           'pyme_omero', 'install_plugin.py')
    subprocess.Popen('%s %s' % (sys.executable, plugin_install_path), 
                        shell=True)


class DevelopModuleAndInstallPlugin(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        install_pyme_plugin()
        

class InstallModuleAndInstallPlugin(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        install_pyme_plugin()


setup(
    name='pyme_omero',
    version='20.09.10',
    description='pyme-omero interoperability',
    packages=find_packages(),
    cmdclass={
        'develop': DevelopModuleAndInstallPlugin,
        'install': InstallModuleAndInstallPlugin,
    },
)
