# pyme-omero
This is a PYME plugin which enables interoperability between PYME and an OMERO server. Currently the functionality is pretty sparse, but feature requests are welcome. Main use case at the moment is uploading PYME `ImageStack` objects to
an OMERO server (either as ome.tif format or png) and attaching PYME `tabular` (localization) files to it. The attached localizations can then be viewed from PYMEVis by opening PYMEVis and clicking `File > Open OMERO` and copy pasting the OMERO `Link to this image` into the dialog box.

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