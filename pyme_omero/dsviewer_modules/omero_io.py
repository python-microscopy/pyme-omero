
from PYME.DSView.modules._base import Plugin
import logging

logger = logging.getLogger(__name__)


class OMEROIO(Plugin):
    def __init__(self, dsviewer):
        from tempfile import TemporaryDirectory

        Plugin.__init__(self, dsviewer)

        self._tempdir = TemporaryDirectory()

        logging.debug('Adding menu items for OMERO loading')

        self.dsviewer.AddMenuItem('OMERO', 'Open', self.OnOpenOMERO)
        self.dsviewer.AddMenuItem('OMERO', 'Save to OMERO', self.OnSaveToOMERO)

    def OnOpenOMERO(self, wx_event=None):
        # from pyme_omero.core import localization_files_from_image_url
        from PYME.IO.image import ImageStack
        from PYME.DSView import ViewIm3D
        import wx
        from pyme_omero.core import download_image

        dlg = wx.TextEntryDialog(self.dsviewer, 'OMERO URL', 
                                 'URL to OMERO image', '')
        
        if dlg.ShowModal() == wx.ID_OK:
            image_url = dlg.GetValue()
        else:
            dlg.Destroy()
            return
        
        dlg.Destroy()

        path = download_image(image_url, self._tempdir.name)
        logger.debug('temporary file path: %s' % path)

        im = ImageStack(filename=path)

        dv = ViewIm3D(im, glCanvas=self.dsviewer.glCanvas, 
                      parent=wx.GetTopLevelParent(self.dsviewer))

        #set scaling to (0,1)
        for i in range(im.data.shape[3]):
            dv.do.Gains[i] = 1.0
    
    def OnSaveToOMERO(self, wx_event=None):
        from pyme_omero.recipe_modules import omero_upload
        from PYME.recipes.base import ModuleCollection
        import os

        context = dict(file_stub=os.path.splitext(os.path.split(self.image.filename)[-1])[0])

        rec = ModuleCollection()
        rec.namespace['input'] = self.image

        uploader = omero_upload.RGBImageUpload(rec, inputName='input')
        if uploader.configure_traits(kind='modal'):
                uploader.save(rec.namespace, context)
    
    def __del__(self):
        self._tempdir.cleanup()


def Plug(dsviewer):
    return OMEROIO(dsviewer)
