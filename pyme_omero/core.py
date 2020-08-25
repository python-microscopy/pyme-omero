
import omero.model
from omero.gateway import BlitzGateway
from omero.cli import cli_login
from omero import rtypes
import yaml
import os
from PYME.config import user_config_dir
import logging

logger = logging.getLogger(__name__)

credentials = os.path.join(user_config_dir, 'plugins', 'config', 'pyme-omero')
with open(credentials) as f:
    credentials = yaml.safe_load(f)

LOGIN_ARGS = ['-u%s' % credentials['user'], '-w%s' % credentials['password'], 
              '-s%s' % credentials['address'], '-p%s' % credentials.get('port', 4064)]

def create_dataset(name):
    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        dataset = omero.model.DatasetI()
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
        project = omero.model.ProjectI()
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
        dataset = omero.model.DatasetI()
        dataset.setName(rtypes.rstring(dataset_name))
        dataset = conn.getUpdateService().saveAndReturnObject(dataset)
        return dataset.getId().getValue()

def file_import(client, file, wait=-1):
    """Re-usable method for a basic import."""
    from pyme_omero import import_utils
    mrepo = client.getManagedRepository()
    files = [file]

    fileset = import_utils.create_fileset(files)
    settings = import_utils.create_settings()

    proc = mrepo.importFileset(fileset, settings)
    try:
        return import_utils.assert_import(client, proc, files, wait)
    finally:
        proc.close()

def upload_image_from_file(file, dataset_name, attachments=(), wait=-1):
    attachments = list(attachments)

    dataset_id = get_or_create_dataset_id(dataset_name)

    with cli_login() as cli:
        conn = BlitzGateway(client_obj=cli._client)

        r = file_import(cli._client, file, wait)
        if r:
            links = []
            # TODO - doing this as iterable fileset for single file is weird
            p = r.pixels[0]
            image_id = p.image.id.val
            logger.debug('Imported Image ID: %d' % image_id)
            link = omero.model.DatasetImageLinkI()
            link.parent = omero.model.DatasetI(dataset_id, False)
            link.child = omero.model.ImageI(image_id, False)
            links.append(link)
            conn.getUpdateService().saveArray(links, conn.SERVICE_OPTS)

            if len(attachments) >  0:
                # have to have loadedness -> True to link an annotation
                image = conn.getObject("Image", image_id)
                for attachment in attachments:
                    # TODO - add guess_mimetype here
                    namespace='pyme.localizations'
                    mimetype='application/octet-stream'
                    file_ann = conn.createFileAnnfromLocalFile(attachment, 
                                                        mimetype=mimetype, 
                                                        ns=namespace, desc=None)
                    logger.debug('Attaching FileAnnotation %d to %d' % (file_ann.getId(), image_id))
                    image.linkAnnotation(file_ann)

if __name__ == '__main__':
    upload_image_from_file('/Users/Andrew/Desktop/112418ROI00877.png',
                           'pyme_omero_testing1', 
                           attachments=['/Users/Andrew/Desktop/112418ROI00877.hdf'])
