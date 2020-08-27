import logging

logger=logging.getLogger(__name__)


class OMEROLoader(object):
    def __init__(self, vis_frame):
        self._temp_files = []
        self.vis_frame = vis_frame
        self.pipeline = vis_frame.pipeline

        logging.debug('Adding menu items for OMERO loading')

        vis_frame.AddMenuItem('File', 'Open OMERO', self.OnOpenOMERO)

    def OnOpenOMERO(self, wx_event=None):
        from pyme_omero.core import localization_tempfiles_from_image_url
        import wx
        dlg = wx.TextEntryDialog(self.vis_frame, 'OMERO URL', 
                                 'URL to OMERO image with attached localizations', '')

        if dlg.ShowModal() == wx.ID_OK:
            image_url = dlg.GetValue()
        else:
            dlg.Destroy()
            return
        
        dlg.Destroy()

        ltf = localization_tempfiles_from_image_url(image_url)
        self._temp_files.extend(ltf)

        for temp_file in ltf:
            self.pipeline.OpenFile(temp_file)
    
    def __del__(self):
        for tf in self._temp_files:
            try:
                tf.close()
            except:
                pass


def Plug(vis_frame):
    vis_frame.omero_loader = OMEROLoader(vis_frame)