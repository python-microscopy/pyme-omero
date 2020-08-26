
import numpy as np
from PYME.IO.image import ImageStack
from PYME.IO.tabular import DictSource
from pyme_omero.recipe_modules.omero_upload import RGBImageUpload
from PYME.recipes.base import ModuleCollection

def test_upload():
    rec = ModuleCollection()
    im = ImageStack(data=np.reshape(np.random.randint(0, 100, (25, 25)), (25, 25, 1, 1)), haveGUI=False)
    fake_locs = DictSource(dict(x=np.random.rand(5), y=np.random.rand(5), 
                                t=np.random.randint(0, 10, 5)))
    rec.namespace['test'] = im
    rec.namespace['fake_locs'] = fake_locs
    rec.add_module(RGBImageUpload(rec, 
        inputName='test', omero_dataset='pyme-omero-testing', input_localization_attachments={'fake_locs': 'test.hdf'}
    ))
    rec.execute()
    rec.save(context={'file_stub':'test'})
