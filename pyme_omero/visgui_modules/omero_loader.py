
import wx
import logging

logger=logging.getLogger(__name__)


class SnapshotDialog(wx.Dialog):
    def __init__(self, parent=None, defaults=dict(), size=(300, 400)):
        wx.Dialog.__init__(self, parent, title='Save Snapshot to OMERO',
                           size=size)

        v_sizer = wx.BoxSizer(wx.VERTICAL)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(wx.StaticText(self, label='Project:'))
        self.project = wx.TextCtrl(self, wx.ID_ANY, defaults.get('project', ''), 
                              size=(250,-1))
        h_sizer.Add(self.project, 0, wx.ALL, 5)
        v_sizer.Add(h_sizer, 0, wx.ALL, 5)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(wx.StaticText(self, label='Dataset:'))
        self.dataset = wx.TextCtrl(self, wx.ID_ANY, defaults.get('dataset', ''), 
                              size=(250,-1))
        h_sizer.Add(self.dataset, 0, wx.ALL, 5)
        v_sizer.Add(h_sizer, 0, wx.ALL, 5)

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        h_sizer.Add(btn, 0, wx.ALL, 5)
        v_sizer.Add(h_sizer, 0, wx.ALL, 5)

        self.SetSizerAndFit(v_sizer)

class OMEROLoader(object):
    def __init__(self, vis_frame):
        from tempfile import TemporaryDirectory
        self._tempdir = TemporaryDirectory()
        self.vis_frame = vis_frame
        self.pipeline = vis_frame.pipeline

        logging.debug('Adding menu items for OMERO loading')
        vis_frame.AddMenuItem('File', 'Open OMERO', self.OnOpenOMERO)
        vis_frame.AddMenuItem('File>Save to OMERO', 'Snapshot', self.OnSaveSnapshot)
        vis_frame.AddMenuItem('File>Save to OMERO', 'PNG', self.OnSavePNG)
        vis_frame.AddMenuItem('File>Save to OMERO', 'OME Tif', self.OnSaveTif)
        vis_frame.AddMenuItem('File>Save to OMERO', 'From Recipe', self.OnSaveFromRecipe)

    def OnOpenOMERO(self, wx_event=None):
        from pyme_omero.core import localization_files_from_image_url
        import wx
        import os
        dlg = wx.TextEntryDialog(self.vis_frame, 'OMERO URL', 
                                 'URL to OMERO image with attached localizations', '')

        if dlg.ShowModal() == wx.ID_OK:
            image_url = dlg.GetValue()
        else:
            dlg.Destroy()
            return
        
        dlg.Destroy()

        paths = localization_files_from_image_url(image_url, self._tempdir.name)

        data_sources = {}
        for p_ind in range(1, len(paths)):
            ds = self.pipeline._ds_from_file(paths[p_ind])
            name = os.path.splitext(os.path.split(paths[p_ind])[-1])[0]
            data_sources[name] = ds
            self.pipeline.addDataSource(name, ds)
        
        self.pipeline.OpenFile(paths[0])
        self.vis_frame.SetFit()
        self.vis_frame.add_pointcloud_layer()
    
    def OnSaveSnapshot(self, wx_event=None):
        from pyme_omero.core import upload_image_from_file
        import os
        import PIL
        import wx
        from OpenGL.GL import GL_LUMINANCE, GL_RGB
        # from PYME.LMVis.Extras.snapshot import save_snapshot

        file_stub=os.path.splitext(os.path.split(self.pipeline.filename)[-1])[0]
        
        # take the snapshot
        snap = self.vis_frame.glCanvas.getIm(None, GL_RGB)
        logger.debug('%s %s %d' % (snap.dtype, snap.shape, snap.max()))
        if snap.ndim == 3:
            img = PIL.Image.fromarray(snap.transpose(1, 0, 2))
        else:
            img = PIL.Image.fromarray(snap.transpose())
        
        img = img.transpose(PIL.Image.FLIP_TOP_BOTTOM)
        
        snapshot = os.path.join(self._tempdir.name, file_stub + '.png')
        img.save(snapshot)

        dlg = SnapshotDialog(self.vis_frame)
        ret = dlg.ShowModal()
        
        if ret == wx.ID_OK:
            project = str(dlg.project.GetValue())
            dataset = str(dlg.dataset.GetValue())

            current = os.path.join(self._tempdir.name, self.pipeline.selectedDataSourceKey + '.hdf')
            try:
                mdh = self.pipeline.selectedDataSource.mdh
            except AttributeError:
                mdh = self.pipeline.mdh
            self.pipeline.selectedDataSource.to_hdf(current, 'Localizations', 
                                                    metadata=mdh)
            attachments = [current]

            if 'Localizations' in self.pipeline.dataSources.keys() and self.pipeline.selectedDataSourceKey !='Localizations':
                locs = os.path.join(self._tempdir.name, 'Localizations.hdf')
                try:
                    mdh = self.pipeline.dataSources['Localizations'].mdh
                except AttributeError:
                    mdh = self.pipeline.mdh
                self.pipeline.dataSources['Localizations'].to_hdf(locs, 
                                                                  'Localizations',
                                                                  metadata=mdh)
                attachments.append(locs)
            
            upload_image_from_file(snapshot, dataset, project, attachments)
    
    def OnSavePNG(self, wx_event=None):
        from pyme_omero.recipe_modules import omero_upload
        import os
        from PYME.recipes.base import ModuleCollection
        from PYME.recipes.localisations import DensityMapping

        context = dict(file_stub=os.path.splitext(os.path.split(self.pipeline.filename)[-1])[0])
        
        rec = ModuleCollection() # build new recipe but point to old namespace
        rec.namespace = self.pipeline.recipe.namespace
        rec.add_module(DensityMapping(rec, 
                                        inputLocalizations=self.pipeline.selectedDataSourceKey,
                                        outputImage='thumbnail_rendering'))
        rec.add_module(omero_upload.RGBImageUpload(rec,
                                                    input_image='thumbnail_rendering'))
        if rec.configure_traits(view=rec.pipeline_view, kind='modal'):
            rec.execute()
            rec.save(context)
    
    def OnSaveTif(self, wx_event=None):
        from pyme_omero.recipe_modules import omero_upload
        import os
        from PYME.recipes.base import ModuleCollection
        from PYME.recipes.localisations import DensityMapping

        context = dict(file_stub=os.path.splitext(os.path.split(self.pipeline.filename)[-1])[0])
        
        rec = ModuleCollection() # build new recipe but point to old namespace
        rec.namespace = self.pipeline.recipe.namespace
        rec.add_module(DensityMapping(rec, 
                                        inputLocalizations=self.pipeline.selectedDataSourceKey,
                                        outputImage='thumbnail_rendering'))
        rec.add_module(omero_upload.ImageUpload(rec,
                                                input_image='thumbnail_rendering'))
        if rec.configure_traits(view=rec.pipeline_view, kind='modal'):
            rec.execute()
            rec.save(context)
    
    def OnSaveFromRecipe(self, wx_event=None):
        from pyme_omero.recipe_modules import omero_upload
        import os

        context = dict(file_stub=os.path.splitext(os.path.split(self.pipeline.filename)[-1])[0])

        omero_mods = [mod for mod in self.pipeline.recipe.modules if isinstance(mod, omero_upload.ImageUpload)]
        
        for mod in omero_mods:
            mod.save(self.pipeline.recipe.namespace, context)
    
    def __del__(self):
        self._tempdir.cleanup()


def Plug(vis_frame):
    vis_frame.omero_loader = OMEROLoader(vis_frame)
