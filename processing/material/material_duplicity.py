import os
import numpy as np
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from pathlib import Path
from utils.logger import logger
from utils.utility import load_input_excel
from processing.material.multiple_materialgroups import process_multiple_materialgroups
from processing.material.material_disparity import disparity_materials

def material_duplicity(material_df):
    if material_df is None or material_df.empty:
        raise ValueError("No valid material data provided")

    df1 = material_df[['Serviceeventcode', 'Itemnumber']].drop_duplicates()
    df1c = pd.DataFrame(df1['Itemnumber'].value_counts()).reset_index()
    df1c = df1c.loc[df1c['count']>1]
    df1m = df1.merge(df1c, on='Itemnumber', how='inner')
    df1m.sort_values(by='Itemnumber', inplace=True)
    # Merge Material names to the output
    df1m = df1m.merge(material_df[['Itemnumber','MaterialName']], on='Itemnumber', how='left')
    # Merge AND_OR column to the output
    df1m = df1m.merge(material_df[['Serviceeventcode','AND_OR']], on='Serviceeventcode', how='left')
    df1m.to_excel(os.path.join(config.locations.processed, config.processed_files.serviceEvent_material + "_processed.xlsx"), index=False)    
    logger.info(f"(1/6) Material duplicity data processed for {len(df1m)} Itemnumbers")


def materialGroup_duplicity(qw):
    
    qw1 = qw[['Serviceeventcode', 'MaterialGroup', 'AND_OR']].drop_duplicates()
    qw1c = pd.DataFrame(qw1['MaterialGroup'].value_counts()).reset_index()
    qw1c = qw1c.loc[qw1c['count']>1]
    qw1m = qw1.merge(qw1c, on='MaterialGroup', how='inner')
    qw1m.sort_values(by='MaterialGroup', inplace=True)
    # Merge Material group names to the output
    qw1m = qw1m.merge(qw[['MaterialGroup','MaterialGroupDescription']], on='MaterialGroup', how='left')
    qw1m.to_excel(os.path.join(config.locations.processed, config.processed_files.serviceEvent_materialgroup + "_processed.xlsx"), index=False)
    logger.info(f"(2/6) Material group duplicity data processed for {len(qw1m)} MaterialGroups")


def material_vs_materialgroup(material_df, materialgroup_df):
    req_cols = ['Serviceeventcode', 'Itemnumber', 'MaterialName', 'MaterialGroup', 'MaterialGroupDescription','AND_OR']
    mg_all  = material_df[req_cols].drop_duplicates()
    qw1 = materialgroup_df[['Serviceeventcode', 'MaterialGroup', 'AND_OR']].drop_duplicates()
    mg1 = mg_all.merge(qw1, on='MaterialGroup', how='inner', suffixes=('_primary', '_secondary'))
    mismatches = mg1.loc[mg1['Serviceeventcode_primary'] != mg1['Serviceeventcode_secondary']]
    mismatches.to_excel(os.path.join(config.locations.processed, config.processed_files.material_materialgroup_conflicts + "_processed.xlsx"), index=False)
    logger.info(f"(3/6) Material vs MaterialGroup conflicts data processed for {len(mismatches)} records")


def materialgroup_mixie(material_df):
    req_cols = ['Serviceeventcode', 'MaterialGroup', 'AND_OR']
    dmg_all = material_df[req_cols].drop_duplicates()
    dmgg = dmg_all.groupby('MaterialGroup').size().reset_index(name='count')
    dmgg.sort_values(by='count', ascending=False, inplace=True)

    # Two is a general constant number used for analysis - can be made dynamic through config
    dmgg2 = dmgg.loc[dmgg['count']==2]
    dmgg2 = material_df.loc[material_df['MaterialGroup'].isin(dmgg2['MaterialGroup'])]
    dmgg2 = dmgg2.sort_values(by='MaterialGroup')
    req_cols = ['Serviceeventcode', 'MaterialGroup', 'MaterialGroupDescription', 'AND_OR']
    dmgg2f = dmgg2[req_cols].drop_duplicates()

    req_cols = ['Serviceeventcode',  'Itemnumber', 'MaterialName', 'MaterialGroup']
    mrg_mixie = dmgg2f.merge(material_df[req_cols], on=['Serviceeventcode','MaterialGroup'], how='left')
    mrg_mixie.to_excel(os.path.join(config.locations.processed, config.processed_files.materialgroup_mixie + "_processed.xlsx"), index=False)
    logger.info(f"(4/6) Material group mixie data processed for {len(mrg_mixie)} records")
 

def processing_material_allthreads(material_df = None, materialgroup_df = None):

    if material_df is None:
        material_df = load_input_excel(config.input_files.serviceEvent_material)
    if materialgroup_df is None:
        materialgroup_df = load_input_excel(config.input_files.serviceEvent_materialgroup)

    material_duplicity(material_df)
    materialGroup_duplicity(materialgroup_df)
    material_vs_materialgroup(material_df, materialgroup_df)
    materialgroup_mixie(material_df)
    process_multiple_materialgroups(material_df)
    disparity_materials(material_df)

