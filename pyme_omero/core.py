
import omero.model as o_model
from omero.gateway import BlitzGateway
from omero.cli import cli_login
from omero import rtypes
from omero.gateway import BlitzGateway
import yaml

credentials = '/Users/Andrew/.PYME/plugins/config/pyme-omero'
with open(credentials) as f:
    credentials = yaml.safe_load(f)

LOGIN_ARGS = ['-u%s' % credentials['user'], '-w%s' % credentials['password'], 
              '-s%s' % credentials['address'], '-p%s' % credentials.get('port', 4064)]

def create_dataset(name):
    with cli_login(*login_args) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        dataset = o_model.DatasetI()
        dataset.setName(rtypes.rstring(name))
        dataset = conn.getUpdateService().saveAndReturnObject(dataset)
        return dataset.getId().getValue()