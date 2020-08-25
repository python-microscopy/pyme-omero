
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
    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        dataset = o_model.DatasetI()
        dataset.setName(rtypes.rstring(name))
        dataset = conn.getUpdateService().saveAndReturnObject(dataset)
        return dataset.getId().getValue()

def get_or_create_project_id(project_name):
    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        
        # check if the project already exists
        projects = conn.getContainerService().loadContainerHierarchy('Project', 
                                                                     None, None)
        for p in projects:
            if p.getName().getValue() == project_name:
                return p.getId().getValue()
        
        # create a new project
        project = o_model.ProjectI()
        project.setName(rtypes.rstring(project_name))
        project = conn.getUpdateService().saveAndReturnObject(project)
        return project.getId().getValue()

def get_or_create_dataset_id(dataset_name):
    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        
        # check if the dataset already exists
        datasets = conn.getContainerService().loadContainerHierarchy('Dataset', 
                                                                     None, None)
        for d in datasets:
            if d.getName().getValue() == dataset_name:
                return d.getId().getValue()
        
        # create a new dataset
        dataset = o_model.DatasetI()
        dataset.setName(rtypes.rstring(dataset_name))
        dataset = conn.getUpdateService().saveAndReturnObject(dataset)
        return dataset.getId().getValue()
