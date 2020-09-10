# pyme-omero
This is a PYME plugin which enables interoperability between PYME and an OMERO server. Feature requests welcome.

## Current Features / how-to
- Load localizations attached to an OMERO image in PYMEVis
  1. Open PYMEVis 
  2. Clicking `File > Open OMERO` 
  3. copy the OMERO `Link to this image` into the dialog box.
  4. Click OK.
- Upload localizations from PYMEVis to OMERO server with a thumbnail rendering
  1. Open localizations in PYMEVis
  2. make sure there is an image rendering in the pipeline recipe, either by adding the `DensityMapping` recipe module, or by loading one of the example recipes `pyme_omero/example_recipes`.
  3. Click `File > Save to OMERO`.
  4. Enter the project name (optional) and dataset name the image should be uploaded/linnked to. The project/dataset will be created if they don't already exist.
  5. In the `Input Localization Attachments` table, click to open the table menu and add a localization attachment. You can attach multiple localization sets from the recipe to the image. Their filenames will be whatever you enter in the `Table Name` box, defaulting to an `.hdf` extension if you do not specify one.
  6. Click OK.
- Load image from an OMERO server in dh5view
  1. From an open dh5view window, click `Modules > omero_io`.
  2. Click `OMERO > Open`, 
  3. Copy the `Link to this image` from e.g. OMERO.web into the text box
  4. Click OK.
- Upload image from dh5view window to an OMERO server
  1. From an open dh5view window, click `Modules > omero_io`.
  2. Click `OMERO > Save to OMERO`.
  3. Enter the project name (optional) and dataset name the image should be uploaded/linnked to. The project/dataset will be created if they don't already exist.
  4. Click OK.
- Upload images/localizations from a recipe run on a PYME cluster or in the PYME bakeshop
  1. create a recipe using any of the upload modules in the `omero_upload` section of the `Add Module` menu in the recipe GUI.


## Installation
1. install [PYME](https://python-microscopy.org/)
2. install [omero-py](https://pypi.org/project/omero-py/)
3. clone this repository
4. run 
    ```
    python pyme-omero/setup.py develop
    ```
5. run 
   ```
   python pyme-omero/pyme_omero/install_plugin.py
   ```
   A GUI dialog should open for you to ender your OMERO server information/credentials, which will be stored in the PYME config directory (typically `.PYME` folder in your user directory).
   * Note - mac users installing to conda environments will need to run `install_plugin.py` using a 'framework build', accomplished by running 
        ```
        /opt/miniconda3/python.app/Contents/MacOS/python pyme_omero/install_plugin.py
        ``` 
        or similar depending on your conda install location.

### Manual configuration
If the configuration GUI failed, you can also create the configuration file manually,
by making a `pyme-omero` file in `.PYME/plugins/config` containing the omero server information in yaml format, e.g.
   ```
   user: <your OMERO user name>
   password: <your OMERO password>
   address: <OMERO server IP address>
   port: <OMERO server port>
   ```
   noting that port is optional if your OMERO server uses the default port (4064).