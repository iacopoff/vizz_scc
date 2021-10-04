import owslib
from owslib.wfs import WebFeatureService
import zipfile,io
import os
import geopandas as gpd

import requests

def get_gaul(layer='g2015_2014_1'):
    """ get adm units from GAUL (FAO) dataset. return geopackage """
    
    wfs = WebFeatureService(url='https://data.apps.fao.org/map/gsrv/gsrv1/gaul/wfs', version='1.1.0')

    #print([operation.name for operation in wfs.operations])
    #print(list(wfs.contents))
    #for i in wfs.operations:
    #    print(i.name," ",i.parameters)

    response = wfs.getfeature(typename=f'gaul:{layer}', srsname='EPSG:4326',outputFormat="SHAPE-ZIP")
    z = zipfile.ZipFile(response)
    fnames = []
    for i in z.infolist():
        fnames.append(i.filename)
        z.extract(i.filename)
        if "shp" in i.filename:
            file_name = i.filename
        
    
    print(f"saving {layer} in geopackage 'geodb.gpkg'")
    
    os.system(f"ogr2ogr -f GPKG geodb.gpkg {file_name}")  
    
    for f in fnames:
        if os.path.exists(f):
            os.remove(f)
        else:
            print("File does not exists")

    
    return 


def get_spam(fformat ="geotiff",geotiff_var = "SOYB"):
    if fformat == "csv":
        db = f"https://s3.amazonaws.com/mapspam/2010/v2.0/csv/spam2010v2r0_global_phys_area.{fformat}.zip"
        r = requests.get(db)
        z = zipfile.ZipFile(r)
        for i in z.infolist():
            z.extract(i.filename)   
    elif fformat == "geotiff":
        db = f"https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.{fformat}.zip"
        r = requests.get(db)
        z = zipfile.ZipFile(r)
        for i in z.infolist():
            if geotiff_var in i.filename:
                z.extract(i.filename)   
                
        #cmd = f"gdal_translate -of GPKG {i.filename}.tif geodb.gpkg"
        
    elif fformat == "dbf":
        db = f"https://s3.amazonaws.com/mapspam/2010/v2.0/geotiff/spam2010v2r0_global_phys_area.{fformat}.zip"
        r = requests.get(db)
        z = zipfile.ZipFile(r)
        for i in z.infolist():
            z.extract(i.filename)        
    else:
        print("wrong format")
    
    
if __name__ == "__main__":
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("downloading GAUL")
        get_gaul()
        
    print("downloading SPAM")
    get_spam()