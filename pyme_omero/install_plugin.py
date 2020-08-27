from PYME import config
import os
import sys
from distutils.dir_util import copy_tree
import logging
logger = logging.getLogger(__name__)

def main():
    this_dir = os.path.dirname(__file__)

    try:
        if sys.argv[1] == 'dist':
            copy_tree(os.path.join(this_dir, 'plugins'), 
                      os.path.join(config.dist_config_directory, 'plugins'))
    except IndexError:  # no argument provided, default to user config directory
        copy_tree(os.path.join(this_dir, 'plugins'), 
                  os.path.join(config.user_config_dir, 'plugins'))
    
    try:
        import wx
        from pyme_omero.ui.credentials import CredentialConfigFrame
        app = wx.App()
        frame = CredentialConfigFrame(None)
        frame.Show()
        app.MainLoop()
    except ImportError:
        logger.error('Cannot import WX for graphical configuration - see readme.md to manually configure the plugin [store omero credentials]')

if __name__ == '__main__':
    main()