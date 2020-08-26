
from PYME.recipes.base import register_module
from PYME.recipes.output import RGBImageOutput
from PYME.recipes.traits import DictStrStr, CStr, Input, Output, Enum
import os


@register_module('RGBImageUpload')
class RGBImageUpload(RGBImageOutput):
    """
    Create RGB (png) image and upload it to an OMERO server, optionally
    attaching localization files.

    Parameters
    ----------
    inputName : str
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
    
    inputName = Input('')
    input_localization_attachments = DictStrStr()

    filePattern = '{file_stub}.png'

    scheme = Enum(['OMERO'])
    
    omero_project = CStr('')
    omero_dataset = CStr('')

    def save(self, namespace, context={}):
        """
        Parameters
        ----------
        namespace : dict
            The recipe namespace
        context : dict
            Information about the source file to allow pattern substitution to 
            generate the output name. At least 'filestub' (which is the filename
            without any extension) should be resolved.

        """
        from PIL import Image
        from pyme_omero.core import upload_image_from_file
        from tempfile import TemporaryDirectory
        
        out_filename = self.filePattern.format(**context)

        rgb = Image.fromarray(self.generate(namespace), mode='RGB')

        with TemporaryDirectory() as temp_dir:
            out_filename = os.path.join(temp_dir, out_filename)
            rgb.save(out_filename)

            loc_filenames = []
            for loc_key, loc_stub in self.input_localization_attachments.items():
                loc_filename = os.path.join(temp_dir, loc_stub)
                loc_filenames.append(loc_filename)
                namespace[loc_key].to_hdf(loc_filename)
            
            upload_image_from_file(out_filename, self.omero_dataset, 
                                   self.omero_project, loc_filenames)
    
    @property
    def inputs(self):
        return set(self.input_localization_attachments.keys()).union(set([self.inputName]))
    
    @property
    def default_view(self):
        import wx
        if wx.GetApp() is None:
            return None
        
        from traitsui.api import View, Item
        from PYME.ui.custom_traits_editors import DictChoiceStrEditor, CBEditor

        inputs, outputs, params = self.get_params()
        
        return View([Item(name='inputName', editor=CBEditor(choices=self._namespace_keys)),] +
                    [Item(name='input_localization_attachments', 
                          editor=DictChoiceStrEditor(choices=self._namespace_keys)),] +
                    [Item('_'),] +
                    self._view_items(params), buttons=['OK', 'Cancel'])
