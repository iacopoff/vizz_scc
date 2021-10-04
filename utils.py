# utils
from typing import List
import pandas as pd
from glob import glob
import geopandas as gpd
from rasterstats import zonal_stats as raster_zonal_stats
import ipyleaflet
import json

from collections import OrderedDict

def extract_data(file="spam2010V2r0_global_A_TI.csv"):
    cols = ["iso3","prod_level","alloc_key","cell5m","x","y",'name_cntr','name_adm1', 'name_adm2'] 
    no_techs = ["i","h","l","s","a"]
    
    df_attrs = pd.read_csv(file,encoding="latin-1",usecols=cols)
    
    df_variables = pd.concat([
                pd.read_csv(f,
                    encoding="latin-1",
                    na_values = 0.0,
                    usecols=[f"soyb_{f.split('.')[0][-1].lower()}"]) for f in glob("*csv") if f"{f.split('.')[0][-1].lower()}" in no_techs 
                ],
                    axis=1)
    
    df = pd.concat([df_attrs,df_variables],axis=1)
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.x, df.y),crs="epsg:4326")
    return gdf


def db_getVector_roi(layer="g2015_2014_1",roi: gpd.GeoDataFrame = None,drop=None,rename=None):
    df = gpd.read_file("geodb.gpkg",layer=layer)
    if drop:
        df.drop(drop,axis=1,inplace=True)
    if rename:
        df.rename(columns=rename,inplace=True)
    if isinstance(roi,gpd.GeoDataFrame):
        return subset(df,roi)
    else:
        df


from copy import deepcopy

def subset(df1,df2,how="large"):
    df_1 = deepcopy(df1)
    geoms = []
    for polygon in df2.geometry:
        if how == "large":
            geoms.append(df1[(df1.within(polygon)) | (df1.overlaps(polygon))])
        if how == "small":
            df_1["centroid"] = df_1.centroid
            geoms.append(df1[(df1.centroid.within(polygon))])
    return pd.concat(geoms,axis=0)



def change_dtype(x):
    if pd.api.types.is_object_dtype(x):
        x = x.astype("string")
        return x
    elif pd.api.types.is_float_dtype(x):
        #x =  np.round(x,1)
        x = x.astype(int)
        return x
    else:
        return x
    

def zonal_stats(roi,tiffs,variables_map,stats)-> List[gpd.GeoDataFrame]:
    import re

    layers = OrderedDict()
    for t in tiffs:
        v = re.findall("SOYB_[A-Z]*",t)[0].lower()
        print(v)
        d = {"type":"FeatureCollection","features":[]}
        
        # all_touched == False. This parameter decides how the underlaying raster's grid points are selected
        # in computing zonal statistics. This choice underestimate the soya's physical area of an adm unit. 
        ret = raster_zonal_stats(roi,t,stats=stats,geojson_out=True,all_touched=False,nodata=-1)
        
        for i in ret:
            d["features"].append(i)
        
        layer = gpd.GeoDataFrame.from_features(d)
        # some data preparation/cleaning here
        layer.rename(columns={"sum":variables_map[v]},inplace=True)
        layer.dropna(how="any",inplace=True) #
        layer = layer[layer[variables_map[v]] != 0]
        layer = layer.apply(change_dtype)
        layers[variables_map[v]] = layer
        
    return layers 


def create_choro_layer(dfs,adm, variables,colormap):
    geojsons = []
    choros = []
    var = []
    for k in dfs:
        if k in variables:
            soyb = dfs[k].loc[:,[adm,k,"geometry","country"]].set_index(adm)
            choro = dict(zip(soyb.reset_index()[adm].tolist(), soyb[k].tolist()))
            choros.append(choro)
            soybj = json.loads(soyb.to_json())     
            geojsons.append(soybj)
            var.append(k)
            
    layers = []
    for j,c,v in zip(geojsons,choros,var):
        print(v)
        layer = ipyleaflet.Choropleth(
            geo_data=j,
            choro_data=c,
            colormap=colormap ,
            style={'stroke':False,'fillOpacity': 0.8},
            hover_style={'fillColor': 'red' , 'fillOpacity': 0.2},
            name=v)     
        layers.append(layer)
    return layers
