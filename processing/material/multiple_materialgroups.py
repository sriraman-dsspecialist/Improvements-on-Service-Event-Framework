import os
import numpy as np
from utils.logger import logger
import pandas as pd
from utils.dbconnection import engine
from utils.config import config
from utils.utility import save_excel_sheets
from pathlib import Path

def get_mg_n(df, df_req, mgg1, n=1):
    """Return rows for service events that are associated with exactly n material groups."""
    req_cols2 = ['Serviceeventcode', 'MaterialGroup', 'MaterialGroupDescription']
    mggf2 = df_req.loc[df_req['Serviceeventcode'].isin(mgg1.loc[(mgg1['MaterialGroup']==n),'Serviceeventcode']), req_cols2].drop_duplicates()
    mggf2.sort_values(by='Serviceeventcode', inplace=True)
    mggf2 = mggf2.merge(df[req_cols2+['Itemnumber','MaterialName']], on=req_cols2, how='left')
    return mggf2


def process_multiple_materialgroups(material_df):
    """Create the multi-material-group workbook for service events with several group assignments."""
    df = material_df.loc[material_df['MaterialGroup']!='N/A']
    req_cols = ['Serviceeventcode', 'MaterialGroup', 'MaterialGroupDescription']
    df_req = df[req_cols].drop_duplicates(ignore_index=True)
    
    # Count the material groups
    mgg1 = df_req.groupby('Serviceeventcode').agg({'MaterialGroup': 'count'})
    mgg1 = mgg1.reset_index()

    mg_dict = {
        '1mgs': get_mg_n(material_df, df_req, mgg1, n=1),
        '2mgs': get_mg_n(material_df, df_req, mgg1, n=2),
        '3mgs': get_mg_n(material_df, df_req, mgg1, n=3),
        '4mgs': get_mg_n(material_df, df_req, mgg1, n=4),
        '5mgs': get_mg_n(material_df, df_req, mgg1, n=5),
        '6mgs': get_mg_n(material_df, df_req, mgg1, n=6),
        '7mgs': get_mg_n(material_df, df_req, mgg1, n=7),
        '9mgs': get_mg_n(material_df, df_req, mgg1, n=9),
        '12mgs': get_mg_n(material_df, df_req, mgg1, n=12)
    }
    save_excel_sheets(mg_dict, os.path.join(config.locations.processed, config.processed_files.multiple_materialgroups+ "_processed.xlsx"))
    logger.info(f"(5/6) Data processed for Service Event Inconsistencies with {len(material_df)} records")
    