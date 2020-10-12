
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

BUFF_SIZE = 1048576  # ome.conditions.ApiUsageException: Max read size is: 1048576

def create_dataset(connection, dataset_name):
    dataset = omero.model.DatasetI()
    dataset.setName(rtypes.rstring(dataset_name))
    dataset = connection.getUpdateService().saveAndReturnObject(dataset)
    return dataset.getId().getValue()

def get_or_create_project_id(connection, project_name):    
    # check if the project already exists
    projects = connection.getContainerService().loadContainerHierarchy('Project', 
                                                                    None, None)
    for p in projects:
        if p.getName().getValue() == project_name:
            return p.getId().getValue()
    
    # create a new project
    project = omero.model.ProjectI()
    project.setName(rtypes.rstring(project_name))
    project = connection.getUpdateService().saveAndReturnObject(project)
    return project.getId().getValue()

def get_or_create_dataset_id(dataset_name, project_name=''):
    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)
        
        # handle linking with project if given
        if project_name != '':
            # check if the dataset already exists within the project
            project_id = get_or_create_project_id(conn, project_name)
            # projects = conn.getContainerService().loadContainerHierarchy('Project', 
                                                                       #  None, None)
            project = conn.getObject("Project", project_id)
            dataset_wrapper = project.findChildByName(dataset_name)
            if dataset_wrapper != None:
                return dataset_wrapper.getId()
            
            # project._toggleCollectionsLoaded(True)
            #linked_datasets = project.linkedDatasetList()

            # check if dataset already exists but is unlinked
            dataset_id = None
            datasets = conn.getContainerService().loadContainerHierarchy('Dataset', 
                                                                    None, None)
            for d in datasets:
                if d.getName().getValue() == dataset_name:
                    dataset_id = d.getId().getValue()
            
            if dataset_id == None:
                # make a new dataset
                dataset_id = create_dataset(conn, dataset_name)
            
            # link dataset to project
            links = []
            link = omero.model.ProjectDatasetLinkI()
            link.parent = omero.model.ProjectI(project_id, False)
            link.child = omero.model.DatasetI(dataset_id, False)
            links.append(link)
            conn.getUpdateService().saveArray(links, conn.SERVICE_OPTS)
            return dataset_id
        
        # no project specified, check if the dataset already exists
        datasets = conn.getContainerService().loadContainerHierarchy('Dataset', 
                                                                    None, None)
        for d in datasets:
            if d.getName().getValue() == dataset_name:
                return d.getId().getValue()
        
        # otherwise create a new dataset
        return create_dataset(conn, dataset_name)

def file_import(client, filename, wait=-1):
    """Re-usable method for a basic import."""
    from pyme_omero import import_utils
    mrepo = client.getManagedRepository()
    files = [filename]

    fileset = import_utils.create_fileset(files)
    settings = import_utils.create_settings(name=os.path.basename(filename))

    proc = mrepo.importFileset(fileset, settings)
    try:
        return import_utils.assert_import(client, proc, files, wait)
    finally:
        proc.close()

def upload_image_from_file(file, dataset_name, project_name='', 
                           attachments=(), wait=-1):
    attachments = list(attachments)

    dataset_id = get_or_create_dataset_id(dataset_name, project_name)

    with cli_login(*LOGIN_ARGS) as cli:
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
                    # TODO - add guess_mimetype / namespace here
                    upload_file_annotation(conn, image, attachment, 
                                           namespace='pyme.localizations')

def upload_file_annotation(connection, image, file, 
                           mimetype='application/octet-stream', 
                           namespace='', description=None):
    """ upload a file as an attachment to an already-uploaded image

    Parameters
    ----------
    connection : omero.gateway.BlitzGateway
        an open connection to an OMERO server
    image : int or omero object wrapped
        either an image_id or a Blitz object wrapper instance of the image
    file : str
        path to the file on disk
    mimetype : str, optional
        by default 'application/octet-stream'
    namespace : str, optional
        by default ''
    description : str, optional
        by default None
    """
    if isinstance(image, str):
        image = connection.getObject("Image", image)
    file_ann = connection.createFileAnnfromLocalFile(file, mimetype=mimetype,
                                                     ns=namespace, desc=None)
    logger.debug('Attaching FileAnnotation %d to %d' % (file_ann.getId(), 
                                                        image.getId()))
    image.linkAnnotation(file_ann)

def localization_files_from_image_url(image_url, out_dir):
    """

    Parameters
    ----------
    image_url : str
        url from OMERO web client, gotten typically by clicking the link symbol
        with an image selected, i.e. `Link to this image`.
    out_dir : str
        path / name of tempfile.TemporaryDirectory

    Returns
    -------
    localization_files : list
        paths to localization files saved to disk
    """
    from urllib.parse import urlparse, parse_qs
    from omero.util.populate_roi import DownloadingOriginalFileProvider

    url = urlparse(image_url)
    # for `Link to this image`
    image_id = int(parse_qs(url.query)['show'][0].split('-')[-1])
    
    localization_files = []

    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)

        # Would be nice to specify pyme.localizations namespace, but probably
        # reliable to check file extentsion since one can manually attach
        # localizations with no namespace specified

        # localization_links = list(conn.getAnnotationLinks('Image', 
        #                                              parent_ids=[image_id],
        #                                              ns="pyme.localizations"))
        
        localization_links = list(conn.getAnnotationLinks('Image', 
                                                            parent_ids=[image_id]))
        
        raw_file_store = conn.createRawFileStore()


        for link in localization_links:
            try:  # select for Blitzwrapped omero types with getFile attr
                og_file = link.getChild().getFile()._obj
            except AttributeError:  # not all BlitzWrapped omero types have getFile
                continue

            filename = og_file.getName().getValue()
            if os.path.splitext(filename)[-1] not in ['.hdf', '.h5r']:
                continue
            path = os.path.join(out_dir, filename)
            localization_files.append(path)
            raw_file_store.setFileId(og_file.id.val)
            with open(path, 'wb') as f:
                f.write(raw_file_store.read(0, og_file.size.val))
        
        return localization_files

def download_image(image_url, out_dir):
    """

    Parameters
    ----------
    image_url : str
        url from OMERO web client, gotten typically by clicking the link symbol
        with an image selected, i.e. `Link to this image`.
    out_dir : str
        path / name of tempfile.TemporaryDirectory

    Returns
    -------
    path : str
        path to file saved to disk
    """
    from urllib.parse import urlparse, parse_qs
    from omero.util.populate_roi import DownloadingOriginalFileProvider

    url = urlparse(image_url)
    # for `Link to this image`
    image_id = int(parse_qs(url.query)['show'][0].split('-')[-1])

    with cli_login(*LOGIN_ARGS) as cli:
        conn = BlitzGateway(client_obj=cli._client)

        image = conn.getObject("Image", image_id)
        
        total_size, buff_generator = image.exportOmeTiff(BUFF_SIZE)
        
        path = os.path.join(out_dir, 
                            os.path.splitext(image.getName())[0] + '.tif')
        with open(path, 'wb') as f:
            for buff in buff_generator:        
                f.write(buff)
        
        return path

# conn = BlitzGateway(credentials['user'], credentials['password'], 
#                     host=credentials['address'], port=credentials.get('port', 
#                                                                       4064))
# conn.connect()
# conn.close()

if __name__ == '__main__':
    upload_image_from_file('/Users/Andrew/Desktop/112418ROI00877.png',
                           'pyme_omero_testing2', project_name='andrew-testing',
                           attachments=['/Users/Andrew/Desktop/112418ROI00877.hdf'])
