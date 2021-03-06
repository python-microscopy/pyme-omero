
from PYME.recipes.base import register_module, OutputModule
from PYME.recipes.output import RGBImageOutput
from PYME.recipes.traits import DictStrStr, CStr, Input, Output, Enum, Float, Int, Bool
import os

class Sample(object):
    pass

@register_module('ImageUpload')
class ImageUpload(OutputModule):
    """
    Upload a PYME ImageStack to an OMERO server, optionally
    attaching localization files.

    Parameters
    ----------
    input_image : str
        name of image in the recipe namespace to upload
    input_localization_attachments : dict
        maps tabular types (keys) to attachment filenames (values). Tabular's
        will be saved as '.hdf' files and attached to the image
    filePattern : str
        pattern to determine name of image on OMERO server. 'file_stub' will be
        set automatically.
    omero_dataset : str
        name of OMERO dataset to add the image to. If the dataset does not
        already exist it will be created. Can use sample metadata entries
        using {format} syntax
    omero_project : str
        name of OMERO project to link the dataset to. If the project does not
        already exist it will be created. Can use sample metadata entries
        using {format} syntax
    
    Notes
    -----
    OMERO server address and user login information must be stored in the user
    PYME config directory under plugins/config/pyme-omero, e.g. 
    /Users/Andrew/.PYME/plugins/config/pyme-omero. The file should be yaml
    formatted with the following keys:
        user
        password
        address
        port [optional]
    
    The project/image/dataset will be owned by the user set in the yaml file.
    """
    
    input_image = Input('')
    input_localization_attachments = DictStrStr()

    filePattern = '{file_stub}.tif'

    scheme = Enum(['OMERO'])
    
    omero_project = CStr('')
    omero_dataset = CStr('{Sample.SlideRef}')

    def _save(self, image, path):
        # force tif extension
        path = os.path.splitext(path)[0] + '.tif'
        image.Save(path)

    def save(self, namespace, context={}):
        """
        Parameters
        ----------
        namespace : dict
            The recipe namespace
        context : dict
            Information about the source file to allow pattern substitution to 
            generate the output name. At least 'file_stub' (which is the 
            filename without any extension) should be resolved.

        """
        from pyme_omero import core
        from tempfile import TemporaryDirectory
        
        out_filename = self.filePattern.format(**context)

        im = namespace[self.input_image]

        if hasattr(im, 'mdh'):
            sample = Sample()  # hack around our md keys having periods in them
            for k in [k for k in im.mdh.keys() if k.startswith('Sample.')]:
                setattr(sample, k.split('Sample.')[-1], im.mdh[k])
            sample_md = dict(Sample=sample)
        else:
            sample_md = {}
        
        dataset = self.omero_dataset.format(**sample_md)
        project = self.omero_project.format(**sample_md)

        with TemporaryDirectory() as temp_dir:
            out_filename = os.path.join(temp_dir, out_filename)
            self._save(im, out_filename)

            loc_filenames = []
            for loc_key, loc_stub in self.input_localization_attachments.items():
                loc_filename = os.path.join(temp_dir, loc_stub)
                if os.path.splitext(loc_filename)[-1] == '':
                    # default to hdf unless h5r is manually specified
                    loc_filename = loc_filename + '.hdf'
                loc_filenames.append(loc_filename)
                try:
                    mdh = namespace[loc_key].mdh
                except AttributeError:
                    mdh = None
                namespace[loc_key].to_hdf(loc_filename, loc_key, metadata=mdh)
            
            image_id = core.upload_image_from_file(out_filename, dataset, 
                                                   project, loc_filenames)
        
        # if an h5r file is the principle input, upload it
        try:
            principle = os.path.join(context['input_dir'], 
                                     context['file_stub']) + '.h5r'
            with core.local_or_named_temp_filename(principle) as f:
                core.connect_and_upload_file_annotation(image_id, f,
                                                        namespace='pyme.localizations')
        except (KeyError, IOError):
            pass
    
    @property
    def inputs(self):
        return set(self.input_localization_attachments.keys()).union(set([self.input_image]))
    
    @property
    def default_view(self):
        import wx
        if wx.GetApp() is None:
            return None
        
        from traitsui.api import View, Item
        from PYME.ui.custom_traits_editors import DictChoiceStrEditor, CBEditor

        inputs, outputs, params = self.get_params()
        
        return View([Item(name='input_image', editor=CBEditor(choices=self._namespace_keys)),] +
                    [Item(name='input_localization_attachments', 
                          editor=DictChoiceStrEditor(choices=self._namespace_keys)),] +
                    [Item('_'),] +
                    self._view_items(params), buttons=['OK', 'Cancel'])
    
    @property
    def pipeline_view(self):
        return self.default_view
    
    @property
    def no_localization_view(self):
        import wx
        if wx.GetApp() is None:
            return None
        
        from traitsui.api import View, Item
        from PYME.ui.custom_traits_editors import CBEditor

        inputs, outputs, params = self.get_params()
        
        return View([Item(name='input_image', editor=CBEditor(choices=self._namespace_keys)),] +
                    [Item('_'),] +
                    self._view_items(params), buttons=['OK', 'Cancel'])


@register_module('RGBImageUpload')
class RGBImageUpload(ImageUpload):
    """
    Create RGB (png) image and upload it to an OMERO server, optionally
    attaching localization files.

    Parameters
    ----------
    input_image : str
        name of image in the recipe namespace to upload
    input_localization_attachments : dict
        maps tabular types (keys) to attachment filenames (values). Tabular's
        will be saved as '.hdf' files and attached to the image
    filePattern : str
        pattern to determine name of image on OMERO server
    omero_dataset : str
        name of OMERO dataset to add the image to. If the dataset does not
        already exist it will be created.
    omero_project : str
        name of OMERO project to link the dataset to. If the project does not
        already exist it will be created.
    zoom : float
        how large to zoom the image
    scaling : str 
        how to scale the intensity - one of 'min-max' or 'percentile'
    scaling_factor: float
        `percentile` scaling only - which percentile to use
    colorblind_friendly : bool
        Use cyan, magenta, and yellow rather than RGB. True, by default.
    
    Notes
    -----
    OMERO server address and user login information must be stored in the user
    PYME config directory under plugins/config/pyme-omero, e.g. 
    /Users/Andrew/.PYME/plugins/config/pyme-omero. The file should be yaml
    formatted with the following keys:
        user
        password
        address
        port [optional]
    
    The project/image/dataset will be owned by the user set in the yaml file.
    """
    filePattern = '{file_stub}.png'
    scaling = Enum(['min-max', 'percentile'])
    scaling_factor = Float(0.95)
    zoom = Int(1)
    colorblind_friendly = Bool(True)

    def _save(self, image, path):
        from PIL import Image
        from PYME.IO.rgb_image import image_to_rgb, image_to_cmy
        
        if (self.colorblind_friendly and (image.data.shape[3] != 1)):
            im = image_to_cmy(image, zoom=self.zoom, scaling=self.scaling, 
                              scaling_factor=self.scaling_factor)
        else:
            im = image_to_rgb(image, zoom=self.zoom, scaling=self.scaling, 
                              scaling_factor=self.scaling_factor)
        
        rgb = Image.fromarray(im, mode='RGB')
        rgb.save(path)
