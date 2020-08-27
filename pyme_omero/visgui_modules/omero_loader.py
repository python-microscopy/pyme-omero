import logging

logger=logging.getLogger(__name__)


class OMEROLoader(object):
    def __init__(self, vis_frame):
        from tempfile import TemporaryDirectory
        self._tempdir = TemporaryDirectory()
        self.vis_frame = vis_frame
        self.pipeline = vis_frame.pipeline

        logging.debug('Adding menu items for OMERO loading')

        vis_frame.AddMenuItem('File', 'Open OMERO', self.OnOpenOMERO)

    def OnOpenOMERO(self, wx_event=None):
        from pyme_omero.core import localization_files_from_image_url
        import wx
        dlg = wx.TextEntryDialog(self.vis_frame, 'OMERO URL', 
                                 'URL to OMERO image with attached localizations', '')

        if dlg.ShowModal() == wx.ID_OK:
            image_url = dlg.GetValue()
        else:
            dlg.Destroy()
            return
        
        dlg.Destroy()

        paths = localization_files_from_image_url(image_url, self._tempdir.name)

        for path in paths:
            self.pipeline.OpenFile(path)
    
    def __del__(self):
        self._tempdir.cleanup()

def Plug(vis_frame):
    vis_frame.omero_loader = OMEROLoader(vis_frame)